# src/robot/browser_worker.py

import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from src.utils.logger import log
from src.robot.browser_actions import ACTION_MAP

PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox",
]


class WorkerSignals(QObject):
    status = pyqtSignal(int, str)
    error = pyqtSignal(int, str)
    finished = pyqtSignal(int)


class TaskRunnable(QRunnable):
    def __init__(self, work_item: dict, signals: WorkerSignals):
        super().__init__()
        # Thông tin người dùng / action
        self.user = work_item["user_info"]
        self.action = work_item["action_info"]
        # Proxy được chỉ định
        self.proxy = work_item.get("proxy_config")
        self.signals = signals
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        uid = self.user.get("id", -1)
        action_name = self.action.get("action_name", "<unknown>")

        # 1) Báo status bắt đầu
        self.signals.status.emit(
            uid, f"Starting '{action_name}' with proxy {self.proxy}"
        )

        # 2) Chạy Playwright với proxy đã được gán
        try:
            with sync_playwright() as p:
                opts = {
                    "user_data_dir": self.user["udd"],
                    "headless": self.user["headless"],
                    "args": PLAYWRIGHT_ARGS,
                    "user_agent": self.user.get("ua"),
                    "proxy": self.proxy,
                }
                ctx = p.chromium.launch_persistent_context(**opts)
                page = ctx.new_page()

                fn = ACTION_MAP.get(action_name)
                if not fn:
                    raise ValueError(f"Unknown action '{action_name}'")

                fn(page, uid, self.action, self.signals)
                self.signals.status.emit(uid, f"'{action_name}' done.")
                page.close()

        except PlaywrightTimeoutError as e:
            self.signals.error.emit(uid, f"Timeout: {e}")
        except Exception as e:
            self.signals.error.emit(uid, f"Error: {e}")
        finally:
            # 3) Emit finished mọi trường hợp
            self.signals.finished.emit(uid)
            log(f"User {uid}: Task '{action_name}' finished.")
