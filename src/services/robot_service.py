import os
import queue
from typing import List, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThreadPool
from src.robot.browser_worker import TaskRunnable, WorkerSignals
from src.services.user_service import UserService, UserUDDService, UserProxyService


class RobotService(QObject):
    task_status_update = pyqtSignal(int, str)
    task_finished_signal = pyqtSignal(int)
    task_error_signal = pyqtSignal(int, str)
    all_tasks_completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Thread pool (pool chỉ quản lý thread, không giới hạn runnable)
        self.pool = QThreadPool.globalInstance()

        # Services phụ trợ
        self.user_service = UserService()
        self.udd_service = UserUDDService()
        self.proxy_service = UserProxyService()

        # Load danh sách proxy
        proxy_records = self.proxy_service.read_all()
        self.proxy_queue = queue.Queue()
        for r in proxy_records:
            self.proxy_queue.put(r.get("value"))

        # Đường dẫn UDD
        self.udd_path = os.path.abspath(self.udd_service.get_selected_udd())

        # Hàng đợi chứa các công việc chưa chạy
        self.pending_tasks: List[Dict[str, Any]] = []
        self.running_count = 0

    @pyqtSlot(list, bool)
    def handle_task(self, task_data_list: List[Dict[str, Any]], headless: bool):
        # 1) Xây danh sách pending_tasks
        self.pending_tasks.clear()
        while not self.proxy_queue.empty():
            self.proxy_queue.get()  # đảm bảo queue rỗng
        for p in self.proxy_service.read_all():
            self.proxy_queue.put(p.get("value"))

        for task_item in task_data_list:
            user = task_item["user_info"]
            user["udd"] = os.path.join(self.udd_path, str(user["id"]))
            user["headless"] = headless
            for idx, action in enumerate(task_item.get("actions", [])):
                self.pending_tasks.append({"user_info": user, "action_info": action})

        # 2) Khởi chạy tối đa len(proxy) tasks ban đầu
        initial = min(self.proxy_queue.qsize(), len(self.pending_tasks))
        for _ in range(initial):
            self._start_next_task()

    def _start_next_task(self):
        # Lấy task và proxy tiếp theo
        work = self.pending_tasks.pop(0)
        proxy_cfg = self.proxy_queue.get()  # block nếu queue rỗng
        work["proxy_config"] = proxy_cfg

        # Prepare signals
        signals = WorkerSignals()
        signals.status.connect(self.task_status_update)
        signals.error.connect(self.task_error_signal)
        signals.finished.connect(self._on_task_finished)

        # Tạo và chạy runnable
        runnable = TaskRunnable(work, signals)
        self.running_count += 1
        self.pool.start(runnable)

    def _on_task_finished(self, user_id: int):
        # 1) Thả proxy trở lại pool
        # (lấy nó từ work_item có thể cần store phía runnable,
        #  nhưng ở đây runnable emit không mang proxy, nên chúng ta
        #  đã embed proxy trong work và nó được giữ trong TaskRunnable
        #  nếu cần, bạn có thể emit proxy qua signal hoặc lưu tạm)
        # Giả sử TaskRunnable emit proxy qua một thuộc tính last_proxy:
        last_proxy = getattr(self, "_last_proxy", None)
        if last_proxy:
            self.proxy_queue.put(last_proxy)

        # 2) Đếm task đã chạy xong
        self.running_count -= 1

        # 3) Nếu vẫn còn pending, chạy tiếp
        if self.pending_tasks:
            self._start_next_task()
        # 4) Nếu không còn pending và không còn running, emit completed
        elif self.running_count == 0:
            self.all_tasks_completed.emit()
