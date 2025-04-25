# src/services/robot_service.py
import time
from collections import deque
from typing import Tuple
from PyQt6.QtCore import QThreadPool, QObject, pyqtSignal, pyqtSlot, Qt

from src.services.user_service import UserProxyService
from src.robot.browser_worker import BrowserWorker
from src.my_types import TaskInfo


class RobotService(QObject):
    def __init__(self, thread_num=1, max_retries=2):
        super(RobotService, self).__init__()
        self.available_proxies = deque(UserProxyService.get_proxies())
        self.pending_task = deque()
        self.task_in_progress = {}
        self.max_retries = max_retries
        self.total_tasks_initial = 0
        self.tasks_succeeded_count = 0
        self.task_failed_perm_count = 0

        self.threadpool = QThreadPool.globalInstance()
        max_thread_num = self.threadpool.maxThreadCount()
        if max_thread_num < thread_num:
            self.threadpool
        thread_num = min(
            thread_num, self.threadpool.maxThreadCount(), len(self.available_proxies)
        )
        self.threadpool.setMaxThreadCount(thread_num)
        print(f"JobManager initialized. Max threads: {thread_num}")

    @pyqtSlot(list)
    def add_tasks(self, tasks: list[TaskInfo]):
        for task in tasks:
            self.pending_task.append((task, 0))
        self.total_tasks_initial += len(tasks)
        # TODO emit_status_update
        # TODO emit message
        self.try_start_tasks()

    @pyqtSlot()
    def try_start_tasks(self):
        while self.pending_task and self.available_proxies:
            proxy = self.available_proxies.popleft()
            task_with_retry = self.pending_task.popleft()
            task_info: TaskInfo = task_with_retry[0]
            retry: int = task_with_retry[1]

            worker = BrowserWorker(
                task_info=task_info,
                retry_count=retry,
                proxy_raw=proxy,
            )

            worker.signals.finished.connect(self.on_worker_finished)
            worker.signals.log_message.connect(self.on_log_message)
            worker.signals.error.connect(self.on_worker_error)

            self.task_in_progress[proxy] = (task_with_retry, worker)

            self.threadpool.start(worker)
            # self._emit_status_update()

    @pyqtSlot(TaskInfo, int, str)
    def on_worker_finished(self, task: TaskInfo, retry: int, proxy: str):
        # task: TaskInfo = task
        # retry: int = retry
        # TODO emit to controller
        print(f"[{task.browser_info.user_id}] Finished.")
        if proxy in self.task_in_progress:
            del self.task_in_progress[proxy]
        self.available_proxies.append(proxy)
        # TODO emit to controller
        self.tasks_succeeded_count += 1
        # TODO emit to controller
        # self._emit_status_update()
        if self.check_if_done():
            return True
        self.try_start_tasks()

    @pyqtSlot(str)
    def on_log_message(self, str):
        print(str)

    @pyqtSlot(TaskInfo, int, str)
    def on_worker_error(self, task_info: TaskInfo, retry: int, message: str):
        print(f"[on_worker_error] {message}")
        if retry < self.max_retries:
            new_task_retry = (task_info, retry + 1)
            self.pending_task.append(new_task_retry)
            # TODO emit to controller
            print(f"[{task_info.browser_info.user_id}] Retry  time ({retry}).")
            # call
        else:
            self.task_failed_perm_count += 1
            # TODO emit to controller
            print(f"Failed permanently after {retry} time.")

    def _emit_status_update(self):
        # TODO emit to controller
        print("_emi_status_update")
        pass

    def check_if_done(self):
        if (
            self.tasks_succeeded_count + self.task_failed_perm_count
            == self.total_tasks_initial
        ):
            if not self.pending_task and not self.task_in_progress:
                return True
