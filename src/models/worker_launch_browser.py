# src/models/worker_launch_browser.py
import logging, sys
import queue
from playwright.sync_api import sync_playwright
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.utils.user_handler import get_proxy


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


class LaunchBrowser_Worker(QObject):
    signal_finished = pyqtSignal(int)
    signal_status = pyqtSignal(int, str)
    signal_error = pyqtSignal(int, str)

    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.user_id = task_data.get("user_id")
        self.udd = task_data.get("udd")
        self.ua = task_data.get("ua")
        self.headless = task_data.get("headless")
        self.proxy_queue: queue.Queue = task_data.get("proxy_queue")
        self.proxy_config = None

    @pyqtSlot()  # Decorator nếu kết nối trực tiếp tới thread.started
    def do_work(self):
        max_get_proxy_attempts = 5
        raw_proxy_source = None
        processed_proxy_dict = None

        if self.proxy_queue:
            self.signal_status.emit(
                self.user_id, f"User {self.user_id}: Getting proxy..."
            )
            logger.info(f"User {self.user_id}: Attempting to get proxy from queue.")

            for attempt in range(1, max_get_proxy_attempts + 1):
                if self.thread() and self.thread().isInterruptionRequested():
                    logger.info(
                        f"User {self.user_id}: Interruption requested during proxy fetching. Aborting."
                    )
                    self.signal_status.emit(
                        self.user_id, f"User {self.user_id}: Interrupted."
                    )
                    self.signal_finished.emit(self.user_id)  # Báo finished khi bị ngắt
                    return  # Thoát khỏi run_browser_task
                try:
                    raw_proxy_source = self.proxy_queue.get(block=True, timeout=10)
                    logger.debug(
                        f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - Got raw proxy source: {raw_proxy_source}"
                    )
                    processed_proxy_dict = get_proxy(raw_proxy_source)
                    if processed_proxy_dict:
                        self.proxy_config = processed_proxy_dict
                        logger.info(
                            f"User {self.user_id}: Successfully obtained and checked proxy on attempt {attempt}."
                        )
                        self.signal_status.emit(
                            self.user_id, f"User {self.user_id}: Proxy obtained."
                        )
                        self.proxy_queue.task_done()  # Báo hiệu item này đã xử lý xong trong hàng đợi
                        break  # Thoát vòng lặp thử lấy proxy
                    else:
                        logger.warning(
                            f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - get_proxy_pycurl failed for {raw_proxy_source}."
                        )
                        self.signal_status.emit(
                            self.user_id, f"User {self.user_id}: Proxy failed check."
                        )
                        self.proxy_queue.task_done()
                except queue.Empty:
                    logger.warning(
                        f"User {self.user_id}: Proxy queue is empty after waiting. Cannot get proxy."
                    )
                    self.signal_status.emit(
                        self.user_id, f"User {self.user_id}: Proxy queue empty."
                    )
                    break
                except Exception as e:
                    logger.error(
                        f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - Error calling get_proxy_pycurl for {raw_proxy_source}: {e}",
                        exc_info=True,
                    )
                    self.signal_status.emit(
                        self.user_id, f"User {self.user_id}: Get proxy error."
                    )
                    if raw_proxy_source is not None:
                        self.proxy_queue.task_done()
            if not self.proxy_config:
                logger.warning(
                    f"User {self.user_id}: Failed to obtain a valid proxy after {max_get_proxy_attempts} attempts."
                )
                self.signal_error.emit(
                    self.user_id, f"User {self.user_id}: Failed to obtain proxy."
                )
                self.signal_status.emit(
                    self.user_id, f"User {self.user_id}: No proxy assigned."
                )
        else:
            logger.info(
                f"User {self.user_id}: Proxy queue is not available, proceeding without proxy."
            )
            self.signal_status.emit(
                self.user_id, f"User {self.user_id}: No proxy queue."
            )

        args = [
            "--disable-blink-features=AutomationControlled",  # Thử ẩn navigator.webdriver (init script cũng làm)
            "--disable-infobars",  # Ẩn thanh "Chrome đang bị điều khiển..."
            "--disable-extensions",  # Tắt tiện ích mở rộng
        ]

        with sync_playwright() as p:
            try:
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=self.udd,
                    proxy=self.proxy_config,
                    user_agent=self.ua,
                    headless=self.headless,
                    args=args,
                )
                stealth_script = """ Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); """
                try:
                    browser_context.add_init_script(stealth_script)
                except Exception as e:
                    logger.warning(
                        f"User {self.user_id}: Error adding init script: {e}"
                    )
                page = browser_context.new_page()
                self.signal_status.emit(self.user_id, "Browser ready.")
                page.wait_for_event("close", timeout=0)
                self.signal_status.emit(self.user_id, "Task complete.")
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
                        print("Page closed on error.")
                    except:
                        pass
                if (
                    browser_context
                ):  # AttributeError: 'BrowserContext' object has no attribute 'is_connected'
                    if browser_context.is_connected():
                        try:
                            browser_context.close()
                            print("Browser closed on error.")
                        except:
                            pass
                if p:
                    try:
                        p.stop()
                        print("Playwright stopped on error.")
                    except:
                        pass
                self.signal_error.emit(self.user_id, f"ERROR: {e}")
                self.signal_status.emit(self.user_id, "Error occurred.")
                self.signal_finished.emit(self.user_id)
            finally:
                self.signal_finished.emit(self.user_id)
