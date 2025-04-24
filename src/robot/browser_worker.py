import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from src.utils.robot_handler import get_proxy
from src.robot.browser_actions import ACTION_MAP
from src.utils.logger import log

PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox",
]


class WorkerSignals(QObject):
    status = pyqtSignal(int, str)
    error = pyqtSignal(int, str)
    # Đổi lại finished mang theo proxy để service có thể trả về pool
    finished = pyqtSignal(int, object)


class TaskRunnable(QRunnable):
    def __init__(self, work_item: dict, signals: WorkerSignals):
        super().__init__()
        self.user = work_item["user_info"]
        self.action = work_item["action_info"]
        self.proxy = work_item["proxy_config"]
        self.signals = signals
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        uid = self.user.get("id", -1)
        action_name = self.action.get("action_name", "<unknown>")

        # 1) emit status
        self.signals.status.emit(
            uid, f"User {uid}: running '{action_name}' on proxy {self.proxy}"
        )

        try:
            # 2) Launch Playwright với proxy
            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    user_data_dir=self.user["udd"],
                    headless=self.user["headless"],
                    args=PLAYWRIGHT_ARGS,
                    user_agent=self.user.get("ua"),
                    proxy=self.proxy,
                )
                page = ctx.new_page()
                fn = ACTION_MAP.get(action_name)
                if not fn:
                    raise ValueError(f"Unknown action '{action_name}'")
                fn(page, uid, self.action, self.signals)
                page.close()
            self.signals.status.emit(uid, f"User {uid}: '{action_name}' done.")
        except PlaywrightTimeoutError as e:
            self.signals.error.emit(uid, f"Timeout: {e}")
        except Exception as e:
            self.signals.error.emit(uid, f"Error: {e}")
        finally:
            # 3) emit finished và đưa proxy lên làm “kết quả” đi kèm
            self.signals.finished.emit(uid, self.proxy)
            log(f"User {uid}: Task '{action_name}' finished.")
