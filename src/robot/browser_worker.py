# src/robot/browser_worker.py
import queue, inspect, os
from playwright.sync_api import sync_playwright
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from src.utils.robot_handler import get_proxy

PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
]


class BrowserWorker(QObject):
    signal_status = pyqtSignal(int, str, QObject)
    signal_error = pyqtSignal(int, str, QObject)
    signal_finished = pyqtSignal(QObject)
    signal_task_completed = pyqtSignal(int, QObject)

    def __init__(self, task_queue: queue.Queue, proxy_queue: queue.Queue, parent):
        super().__init__(parent)
        self._task_queue = task_queue
        self._proxy_queue = proxy_queue
        self.action_info = None
        self.action_index = -1

        self.user_id = -1
        self.user_type = ""
        self.user_ua = ""
        self.user_udd = ""
        self.headless = False
        self.proxy = ""

    @pyqtSlot()
    def run_task(self):
        log_message(f"Worker thread {self.thread()} ({self}) started.")
        while True:
            if self.thread() and self.thread().isInterruptionRequested():
                log_message(
                    f"Worker thread {self.thread()}: Interruption requested. Exiting task loop."
                )
                break
            # lấy dữ liệu từ task_queue
            if self._task_queue:
                try:
                    task_data = self._task_queue.get(block=True, timeout=1)
                    user_info = task_data.get("user_info")
                    self.action_info = task_data.get("action_info")
                    self.action_index = task_data.get("action_index")

                    self.user_id = user_info.get("id", -1)
                    self.user_type = user_info.get("type", "")
                    self.user_ua = user_info.get("ua", "")
                    self.user_udd = user_info.get("udd", "")
                    self.headless = user_info.get("headless", False)
                    # check
                except queue.Empty:
                    log_message(
                        f"Worker thread {self.thread()}: Task queue is empty. Exiting task loop."
                    )
                    break
                except Exception as e:
                    log_message(
                        f"Worker thread {self.thread()}: Error getting task from queue: {e}",
                        exc_info=True,
                    )
                    self.signal_error.emit(
                        self.user_id,
                        f"Error getting task from queue: {e}",
                        self,
                    )
                    continue

                if self.thread() and self.thread().isInterruptionRequested():
                    log_message(
                        f"Worker thread {self.thread()}: Interruption requested after getting task {self.user_id}. Aborting task."
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: Interrupted.",
                        self,
                    )
                    log_message(
                        f"Worker thread {self.thread()}: Task {self.user_id} marked as done in queue (aborted)."
                    )
                    self._task_queue.task_done()
                    break  # Thoát khỏi vòng lặp chính

            # fetch proxy api từ self._proxy_queue
            if self._proxy_queue:
                max_attempt_num = 5
                self.proxy = ""
                for attempt in range(0, max_attempt_num):
                    if self.thread() and self.thread().isInterruptionRequested():
                        self._task_queue.task_done()
                        return
                    try:
                        raw_proxy = self._proxy_queue.get(block=True, timeout=1)
                        proxy = get_proxy(raw_proxy)
                        if proxy:
                            self.proxy = proxy
                            log_message(f"User {self.user_id}: Proxy obtained.")
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Proxy obtained.",
                                self,
                            )
                            self._proxy_queue.task_done()
                            break
                        else:
                            log_message(f"User {self.user_id}: Proxy failed check.")
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Proxy failed check.",
                                self,
                            )
                            self._proxy_queue.task_done()
                    except queue.Empty:
                        log_message(f"User {self.user_id}: Proxy queue empty.")
                        self.signal_status.emit(
                            self.user_id,
                            f"User {self.user_id}: Proxy queue empty.",
                            self,
                        )
                        break
                    except Exception as e:
                        self.signal_status.emit(
                            self.user_id, f"User {self.user_id}: Get proxy error.", self
                        )
                        if proxy is not None:
                            self._proxy_queue.task_done()

                if not self.proxy:
                    self.signal_error.emit(
                        self.user_id,
                        f"User {self.user_id}: Failed to obtain proxy for task.",
                        self,
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: No proxy assigned for task.",
                        self,
                    )
                    self.signal_status.emit(
                        self.user_id, f"User {self.user_id}: Skipping (no proxy).", self
                    )
                    self.signal_task_completed.emit(self.user_id, self)
                    self._task_queue.task_done()
                    continue

            else:
                self.signal_status.emit(
                    self.user_id, f"User {self.user_id}: No proxy queue.", self
                )

            # thực hiện nhiêm vụ có tên action_name
            action_name = self.action_info.get("action_name")
            if action_name == "launch":
                self.handle_launch()
                pass
            elif action_name == "discussion":
                pass
            elif action_name == "marketplace":
                pass
            self.signal_task_completed.emit(self.user_id, self)
        self.signal_finished.emit(self)

    def handle_launch(self):
        with sync_playwright() as p:
            try:
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_udd,
                    user_agent=self.user_ua,
                    proxy=self.proxy,
                    headless=self.headless,
                    args=PLAYWRIGHT_ARGS,
                )
                stealth_script = """ Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); """
                try:
                    browser_context.add_init_script(stealth_script)
                except Exception as e:
                    log_message(f"User {self.user_id}: Error adding init script: {e}")
                page = browser_context.new_page()
                self.signal_status.emit(self.user_id, "Browser ready.", self)
                page.wait_for_event("close", timeout=0)
                self.signal_status.emit(self.user_id, "Task complete.", self)
                if page:
                    page.close()
                if browser_context:
                    browser_context.close()
                if p:
                    p.stop()

            except Exception as e:
                if page and not page.is_closed():
                    try:
                        page.close()
                        log_message("Page closed on error.")
                    except:
                        pass
                if p:
                    try:
                        p.stop()
                        log_message("Playwright stopped on error.")
                    except:
                        pass
                self.signal_error.emit(self.user_id, f"ERROR: {e}", self)
                self.signal_status.emit(self.user_id, "Error occurred.", self)
            finally:
                self.signal_task_completed.emit(self.user_id, self)


def log_message(message):
    """In ra thông điệp kèm theo tên file và số dòng của nơi gọi hàm này."""
    # inspect.stack()[0] là frame của hàm log_message này
    # inspect.stack()[1] là frame của nơi đã gọi hàm log_message
    caller_frame_record = inspect.stack()[1]
    frame = caller_frame_record[0]  # Lấy đối tượng frame
    info = inspect.getframeinfo(frame)

    filename = os.path.basename(info.filename)
    line_number = info.lineno

    print(f"[{filename}:{line_number}] {message}")
