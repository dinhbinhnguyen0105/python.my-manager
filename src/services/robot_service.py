# src/services/robot_service.py

import os
from itertools import islice
from typing import List, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThreadPool, QEventLoop

from src.robot.browser_worker import TaskRunnable, WorkerSignals
from src.services.user_service import UserService, UserUDDService, UserProxyService


class RobotService(QObject):
    task_status_update = pyqtSignal(int, str)
    task_finished_signal = pyqtSignal(int)
    task_error_signal = pyqtSignal(int, str)
    all_tasks_completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Tạo global pool, nhưng số thread sẽ set lại theo batch
        self.pool = QThreadPool.globalInstance()

        # Các service phụ trợ
        self.user_service = UserService()
        self.udd_service = UserUDDService()
        self.proxy_service = UserProxyService()

        # Danh sách proxy gốc
        proxy_records = self.proxy_service.read_all()
        self.proxy_sources = [r.get("value") for r in proxy_records]

        # Thư mục user-data-dir
        self.udd_container_path = os.path.abspath(self.udd_service.get_selected_udd())

    @pyqtSlot(list, bool)
    def handle_task(self, task_data_list: List[Dict[str, Any]], headless: bool):
        # 1) Chuẩn bị toàn bộ list công việc (user+action)
        jobs: List[Dict[str, Any]] = []
        for task_item in task_data_list:
            user = task_item["user_info"]
            user["udd"] = os.path.join(self.udd_container_path, str(user["id"]))
            user["headless"] = headless

            for idx, action in enumerate(task_item.get("actions", [])):
                jobs.append(
                    {
                        "user_info": user,
                        "action_info": action,
                    }
                )

        # 2) Batch size = số proxy
        n_proxy = len(self.proxy_sources)
        if n_proxy == 0:
            # fallback: chạy tuần tự không proxy
            n_proxy = 1

        # Helper chia list thành các nhóm cỡ n
        def chunked(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        # 3) Chạy từng batch
        for batch in chunked(jobs, n_proxy):
            # Điều chỉnh pool size cho batch này
            self.pool.setMaxThreadCount(len(batch))

            # Tạo QEventLoop phụ để chờ batch xong
            loop = QEventLoop()
            remaining = len(batch)

            def _on_finished(user_id):
                nonlocal remaining
                remaining -= 1
                if remaining == 0:
                    loop.quit()

            # Với mỗi job trong batch, lấy proxy tương ứng và tạo Runnable
            for idx, work in enumerate(batch):
                proxy_cfg = self.proxy_sources[idx % n_proxy]
                work["proxy_config"] = proxy_cfg

                signals = WorkerSignals()
                signals.status.connect(self.task_status_update)
                signals.error.connect(self.task_error_signal)
                signals.finished.connect(self.task_finished_signal)
                signals.finished.connect(_on_finished)

                runnable = TaskRunnable(work, signals)
                self.pool.start(runnable)

            # 4) Chờ batch hoàn thành
            loop.exec()

        # 5) Tất cả batch xong
        self.all_tasks_completed.emit()
