# src/robot/browser_worker.py
import time, traceback, sys
from typing import Any, Tuple
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot, Qt
from playwright.sync_api import sync_playwright
from undetected_playwright import Tarnished
from playwright_stealth import stealth_sync

from src.my_types import TaskInfo
from src.utils.robot_handler import get_proxy
from src.robot.browser_actions import ACTION_MAP


class WorkerSignals(QObject):
    progress = pyqtSignal(int)  # message
    error = pyqtSignal(TaskInfo, int, str)  # task_info, retry, message
    finished = pyqtSignal(TaskInfo, int, str)  # task_info, retry, proxy
    log_message = pyqtSignal(str)


class BrowserWorker(QRunnable):
    def __init__(
        self,
        task_info: TaskInfo,
        retry_count: int,
        proxy_raw: str,
    ):
        super(BrowserWorker, self).__init__()
        self.task_info = task_info
        self.browser_info = task_info.browser_info
        self.action_info = task_info.action
        self.proxy_raw = proxy_raw
        self.retry_count = retry_count
        self.signals = WorkerSignals()

        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        if self.action_info.action_name == "<empty>":
            self.signals.log_message.emit(
                f"[{self.browser_info.user_id}] - action is empty: delay in 300s."
            )
            time.sleep(300)
            self.signals.finished.emit(self.task_info, self.retry_count, self.proxy_raw)
            return

        proxy = None
        self.signals.log_message.emit(f"[{self.browser_info.user_id}] Preparing ...")
        try:
            proxy = get_proxy(self.proxy_raw)
            if not proxy:
                raise ValueError("Invalid proxy")
            self.signals.log_message.emit(
                f"[{self.browser_info.user_id}] Fetched proxy: {proxy}"
            )
        except ValueError as e:
            print(f"[{self.task_info.browser_info.user_id}] {e}")
            self.signals.finished.emit(self.task_info, self.retry_count, self.proxy_raw)
            return

        # handle browser task
        try:
            action_name = self.action_info.action_name
            if not self.action_info.action_name:
                raise ValueError("Invalid action info")
            action_function = ACTION_MAP.get(action_name)
            if not action_function:
                raise ValueError(f"Invalid action '{self.action_info.action_name}'")
            with sync_playwright() as p:
                context_kwargs = dict(
                    user_data_dir=self.browser_info.user_data_dir,
                    user_agent=self.browser_info.user_agent,
                    headless=self.browser_info.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        f'--app-name=Chromium - {self.browser_info.user_id or "Unknown User"}',
                    ],
                    ignore_default_args=["--enable-automation"],
                    proxy=proxy,
                )
                if self.browser_info.is_mobile:
                    context_kwargs["viewport"] = {"width": 390, "height": 844}
                    context_kwargs["screen"] = {"width": 390, "height": 844}
                    context_kwargs["is_mobile"] = True
                    context_kwargs["device_scale_factor"] = 3
                    context_kwargs["has_touch"] = True
                context = p.chromium.launch_persistent_context(**context_kwargs)
                Tarnished.apply_stealth(context)
                pages = context.pages
                if pages:
                    current_page = pages[0]
                else:
                    current_page = context.new_page()
                info_html = f"""
<html>
    <head><title>{self.browser_info.user_id}</title></head>
    <body>
        <h2>user agent: {self.browser_info.user_agent}</h2>
    </body>
</html>
"""
                current_page.set_content(info_html)
                page = context.new_page()
                # stealth_sync(page)
                time.sleep(5)
                action_function(
                    page=page,
                    browser_info=self.browser_info,
                    action_info=self.action_info,
                    signals=self.signals,
                )

        # except TimeoutError as e:
        #     self.signals.error.emit(self.task_info, self.retry_count, "Timeout error")
        except Exception as e:
            self.signals.error.emit(self.task_info, self.retry_count, str(e))
        finally:
            self.signals.finished.emit(self.task_info, self.retry_count, self.proxy_raw)
            return
