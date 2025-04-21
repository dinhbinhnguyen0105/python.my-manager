import logging, sys
import queue
from playwright.sync_api import sync_playwright
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class Browser_Worker(QObject):
    signal_status = pyqtSignal(int, str, QObject)
    signal_error = pyqtSignal(int, str, QObject)
    signal_finished = pyqtSignal(QObject)
    signal_task_completed = pyqtSignal(int, QObject)

    def __init__(self, task_queue: queue.Queue, proxy_queue: queue.Queue, parent):
        super().__init__(parent)
        self._task_queue = task_queue
        self._proxy_queue = proxy_queue

    @pyqtSlot
    def run_task(self):
        while True:
            if self.thread() and self.thread().isInterruptionRequested():
                break
            try:
                # lấy dữ liệu từ task_queue
                task_data = self._task_queue.get(block=True, timeout=1000)
                self.browser_info = task_data.get("browser")
                self.action_info = task_data.get("action")
            except queue.Empty:
                break
            except Exception as e:
                continue
