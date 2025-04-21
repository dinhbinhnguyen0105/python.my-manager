# src/robot/browser_worker.py

import queue, os, time
from playwright.sync_api import sync_playwright, Page, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from src.utils.logger import log
from src.utils.robot_handler import get_proxy
from src.robot.browser_actions import ACTION_MAP


PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox",
]


class BrowserWorker(QObject):
    signal_status = pyqtSignal(int, str, QObject)
    signal_error = pyqtSignal(int, str, QObject)
    signal_finished = pyqtSignal(QObject)
    signal_task_completed = pyqtSignal(int, QObject)

    def __init__(self, task_queue: queue.Queue, proxy_queue: queue.Queue, parent=None):
        super().__init__(parent)
        self._task_queue = task_queue
        self._proxy_queue = proxy_queue

        self.user_info = None
        self.user_id = -1
        self.user_type = ""
        self.user_ua = ""
        self.user_udd = ""
        self.headless = False

        self.action_info = None
        self.action_name = ""
        self.playwright_proxy_config = None

    @pyqtSlot()
    def run_task(self):
        log(f"Worker thread {self.thread()} ({self}) started.")
        while True:
            # === 1. Kiểm tra yêu cầu ngắt từ luồng chính ===
            if self.thread() and self.thread().isInterruptionRequested():
                log(
                    f"Worker thread {self.thread()}: Interruption requested. Exiting task loop."
                )
                break
            work_item = None
            # === 2. Lấy đơn vị công việc tiếp theo từ task_queue ===
            try:
                log(f"Worker thread {self.thread()}: Waiting for next task item...")
                work_item = self._task_queue.get(block=True, timeout=1)
                log(
                    f"Worker thread {self.thread()}: Got task item. Tasks remaining: {self._task_queue.qsize()}."
                )
                self.user_info = work_item.get("user_info", {})
                self.action_info = work_item.get("action_info", {})

                self.user_id = self.user_info.get("id", -1)
                self.user_type = self.user_info.get("type", "")
                self.user_ua = self.user_info.get("ua", "")
                self.user_udd = self.user_info.get("udd", "")
                self.headless = self.user_info.get("headless", False)

                self.action_name = self.action_info.get("action_name", "")
                log(
                    f"Worker thread {self.thread()}: Processing task for User ID {self.user_id}, Action '{self.action_name}'."
                )
                self.signal_status.emit(
                    self.user_id,
                    f"User {self.user_id}: Starting action '{self.action_name}'...",
                    self,
                )
            except queue.Empty:
                log(
                    f"Worker thread {self.thread()}: Task queue is empty after timeout. Exiting task loop."
                )
                break
            except Exception as e:
                log(
                    f"Worker thread {self.thread()}: Error getting task item from queue: {e}",
                )
                self.signal_error.emit(
                    self.user_id, f"Error getting task item from queue: {e}", self
                )
                continue
            # === Logic xử lý MỘT ĐƠN VỊ CÔNG VIỆC (cho user_id, action_name đã lấy được) ===
            playwright_proxy_config = None
            browser_context = None
            page = None
            try:
                if self._proxy_queue and not self._proxy_queue.empty():
                    max_attempts = 5
                    raw_proxy = None
                    log(
                        f"User {self.user_id}: Attempting to get proxy source for action '{self.action_name}'."
                    )
                    for attempt in range(1, max_attempts + 1):
                        if self.thread() and self.thread().isInterruptionRequested():
                            log(
                                f"User {self.user_id}: Interruption requested during proxy fetch. Aborting task."
                            )
                            raise InterruptedError(
                                "Task interrupted during proxy fetch"
                            )
                        raw_source = None
                        try:
                            raw_source = self._proxy_queue.get(block=True, timeout=5)
                            log(
                                f"User {self.user_id}: Got raw proxy source: {raw_source}"
                            )
                            processed_proxy_dict = get_proxy(raw_source)
                            self._proxy_queue.task_done()

                            if processed_proxy_dict:
                                playwright_proxy_config = processed_proxy_dict
                                raw_proxy = raw_source  # Lưu cho log
                                log(
                                    f"User {self.user_id}: Successfully obtained proxy on attempt {attempt}."
                                )
                                break
                            else:
                                log(
                                    f"User {self.user_id}: Attempt {attempt}/{max_attempts} - get_proxy failed for {raw_source}. Trying next source."
                                )
                        except queue.Empty:
                            log(
                                f"User {self.user_id}: Proxy source queue is empty after waiting. Cannot get proxy source for this task."
                            )
                            break
                        except Exception as e:
                            log(
                                f"User {self.user_id}: Error calling get_proxy for {raw_source}: {e}",
                            )
                    if not playwright_proxy_config:
                        log(
                            f"User {self.user_id}: Failed to obtain a valid proxy after {max_attempts} attempts for task {self.action_name}. Proceeding without proxy."
                        )
                        self.signal_status.emit(
                            self.user_id,
                            f"User {self.user_id}: No proxy for '{self.action_name}'.",
                            self,
                        )
                else:
                    log(
                        f"User {self.user_id}: Proxy source queue not available or empty. Proceeding without proxy for task {self.action_name}."
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: No proxy queue/empty.",
                        self,
                    )
                # === 4. Execute Playwright Automation cho TÁC VỤ HIỆN TẠI (chỉ 1 hành động) ===
                try:
                    log(
                        f"User {self.user_id}: Launching browser for action '{self.action_name}'."
                    )
                    with sync_playwright() as p:
                        browser_options = {
                            "user_data_dir": self.user_udd,
                            "headless": self.headless,
                            "args": PLAYWRIGHT_ARGS,
                            "user_agent": self.user_ua,
                            "proxy": playwright_proxy_config,
                        }
                        if playwright_proxy_config:
                            log(
                                f"User {self.user_id}: Launching with proxy {playwright_proxy_config.get('server')} for '{self.action_name}'."
                            )
                        else:
                            log(
                                f"User {self.user_id}: Launching without proxy for '{self.action_name}'."
                            )
                        browser_context = p.chromium.launch_persistent_context(
                            **browser_options
                        )
                        page = browser_context.new_page()
                        log(f"User {self.user_id}: Browser launched.")
                        action_function = ACTION_MAP.get(self.action_name)
                        if action_function:
                            log(
                                f"User {self.user_id}: Executing action '{self.action_name}'."
                            )
                            action_function(page, self.user_id, self.action_info, self)
                            log(
                                f"User {self.user_id}: Action '{self.action_name}' completed successfully."
                            )
                            self.signal_task_completed.emit(self.user_id, self)
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Action '{self.action_name}' done.",
                                self,
                            )
                        else:
                            log(
                                f"User {self.user_id}: Unknown action name '{self.action_name}'. Skipping action."
                            )
                            self.signal_error.emit(
                                self.user_id,
                                f"User {self.user_id}: Unknown action '{self.action_name}'.",
                                self,
                            )
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Unknown action.",
                                self,
                            )

                        log(
                            f"User {self.user_id}: Attempting Playwright cleanup for '{self.action_name}'."
                        )
                        if page:
                            try:
                                if not page.is_closed():
                                    page.close()
                            except Exception as e:
                                log(
                                    f"[ERROR] User {self.user_id}: Error closing page: {e}"
                                )

                        log(
                            f"User {self.user_id}: Playwright cleanup finished for '{self.action_name}'."
                        )

                except InterruptedError:
                    log(
                        f"User {self.user_id}: Task interrupted during action '{self.action_name}'. Exiting task processing try block."
                    )
                except PlaywrightTimeoutError as e:
                    log(
                        f"User {self.user_id}: Playwright timeout during action '{self.action_name}': {e}",
                    )
                    self.signal_error.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{self.action_name}' timeout.",
                        self,
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{self.action_name}' timeout.",
                        self,
                    )

                except Exception as e:
                    log(
                        f"User {self.user_id}: Error during action '{self.action_name}': {e}",
                    )
                    self.signal_error.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{self.action_name}' error: {e}.",
                        self,
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{self.action_name}' error.",
                        self,
                    )
            # === Báo hiệu item từ task_queue đã xong ===
            finally:
                if work_item is not None:
                    self._task_queue.task_done()
                    log(
                        f"Worker thread {self.thread()}: Work item for User {self.user_id}, Action '{self.action_name}' marked as done in queue."
                    )
                    log(
                        f"Worker thread {self.thread()}: Task {self.user_id}, Action '{self.action_name}' finished processing. Tasks remaining: {self._task_queue.qsize()}"
                    )

                if self.thread() and self.thread().isInterruptionRequested():
                    log(
                        f"Worker thread {self.thread()}: Interruption requested after processing task {self.user_id}, action '{self.action_name}'. Exiting task loop."
                    )
                    break
        log(
            f"Worker thread {self.thread()} ({self}): Main task loop finished. Exiting thread."
        )
        log(
            f"Worker thread {self.thread()} ({self}): signal_finished emitted. Worker process ended."
        )
        self.signal_finished.emit(self)
