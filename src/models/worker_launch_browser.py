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
        if self.proxy_queue:
            self.signal_status.emit(
                self.user_id, f"User {self.user_id}: Getting proxy..."
            )
            logger.info(f"User {self.user_id}: Attempting to get proxy from queue.")

        stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            });
        """
        with sync_playwright() as p:
            try:
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=self.udd,
                    proxy=proxy,
                    user_agent=self.ua,
                    headless=self.headless,
                )
                browser_context.add_init_script(stealth_script)
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
                if browser_context:
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
            finally:
                self.signal_finished.emit(self.user_id)
