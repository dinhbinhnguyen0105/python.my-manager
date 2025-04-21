import queue

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class LaunchBrowser_Worker(QObject):
    signal_status = pyqtSignal(int, str, QObject)
    signal_error = pyqtSignal(int, str, QObject)
    signal_finished = pyqtSignal(QObject)
    signal_task_completed = pyqtSignal(int, QObject)

    def __init__(self, task_queue: queue.Queue, proxy_queue: queue.Queue, parent=None):
        super().__init__(parent)
        self._task_queue = task_queue
        self._proxy_queue = proxy_queue

        self.user_data_dir = ""
        self.user_id = -1
        self.user_agent = ""
        self.headless = False
        self.is_mobile = False
        self.proxy = None

    @pyqtSlot
    def run_browser_task(self):
        while True:
            # QThread.isInterrruptionRequested() kiểm tra cờ ngắt
            # QCoreApplication.processEvent() cho phép xử lý các sự kiện (bao gồm yêu câu ngắt)
            if self.thread() and self.thread().isInterruptionRequested():
                break
            # --- 1. Lấy dữ liệu từ task_queue ---
            try:
                task_data = self._task_queue.get(block=True, timeout=1000)
                self.user_id = task_data.get("user_id", -1)
                self.user_data_dir = task_data.get("user_data_dir")
                self.user_agent = task_data.get("user_agent")
                self.headless = task_data.get("headless", False)
                self.is_mobile = task_data.get("is_mobile", False)

                self.signal_status.emit(
                    self.user_id, f"User {self.user_id}: Task received.", self
                )

            except queue.Empty:
                break
            except Exception as e:
                self.signal_error.emit(
                    self.user_id, f"Error getting task from queue: {e}", self
                )
                continue
            if self.thread() and self.thread().isInterruptionRequested():
                self._task_queue.task_done()
                break

            # --- 2. Lấy dữ liệu từ proxy ---
            max_attemp_num = 5
            self.proxy = ""
            if self._proxy_queue:
                for attempt in range(0, max_attemp_num):
                    if self.thread() and self.thread().isInterruptionRequested():
                        self._task_queue.task_done()
                        return
                    try:
                        raw_proxy = self._proxy_queue.get(block=True, timeout=1000)
                        proxy = get_proxy(
                            raw_proxy
                        )  # {"service": "hostname:port", "user_name": "...", "password": "..."}
                        if proxy:
                            self.proxy = proxy
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Proxy obtained.",
                                self,
                            )
                            self._proxy_queue.task_done()
                            break
                        else:
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Proxy failed check.",
                                self,
                            )
                            self._proxy_queue.task_done()
                    except queue.Empty():
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

            # --- 3. Thực hiện task ---
            # do something ...
            self.signal_task_completed.emit(self.user_id, self)

        self.signal_finished.emit(self)
