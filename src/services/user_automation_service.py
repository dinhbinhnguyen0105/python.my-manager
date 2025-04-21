# src/services/user_automation_service.py

import queue, os
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

from src.robot.browser_worker import BrowserWorker
from src.services.user_service import UserService, UserUDDService, UserProxyService


class UserAutomationService(QObject):
    task_status_update = pyqtSignal(int, str)
    task_finished_signal = pyqtSignal(int)
    task_error_signal = pyqtSignal(int, str)
    all_tasks_completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_service = UserService()
        self.udd_service = UserUDDService()
        self.proxy_service = UserProxyService()

        self._running_automation_workers = {}
        self._proxy_raw_queue = queue.Queue()
        self._task_queue = queue.Queue()
        self._max_threads = 4
        self.udd_container_path = self.udd_service.get_selected_udd()
        self.udd_container_path = os.path.abspath(self.udd_container_path)
        proxy_records = self.proxy_service.read_all()
        self.proxy_sources = [
            proxy_record.get("value") for proxy_record in proxy_records
        ]

    def _create_worker_pool(self, num_workers):
        current_worker_count = len(self._running_automation_workers)
        workers_to_add = num_workers - current_worker_count
        if workers_to_add <= 0:
            return

        for i in range(workers_to_add):
            thread = QThread()
            worker = BrowserWorker(
                task_queue=self._task_queue,
                proxy_queue=self._proxy_raw_queue,
                parent=None,
            )
            worker.moveToThread(thread)

            worker.signal_status.connect(self._handle_worker_status)
            worker.signal_error.connect(self._handle_worker_error)
            worker.signal_task_completed.connect(self._handle_task_completed)
            worker.signal_finished.connect(self._handle_worker_finished)

            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.started.connect(worker.run_task)

            thread.start()
            self._running_automation_workers[worker] = thread

    # task_data_list = [{"user_info": {"id", "type", "ua"}, "actions": ["action_name": "discussion", "post_info"]}]
    @pyqtSlot(list, bool)
    def handle_task(self, task_data_list: list, headless=False):
        while not self._proxy_raw_queue.empty():
            try:
                self._proxy_raw_queue.get_nowait()
            except queue.Empty:
                pass
        for source in self.proxy_sources:
            self._proxy_raw_queue.put(source)

        self._create_worker_pool(self._max_threads)
        max_actions = 0
        for task_item in task_data_list:
            if "actions" in task_item and isinstance(task_item["actions"], list):
                max_actions = max(max_actions, len(task_item["actions"]))
            else:
                pass
                # user_id = task_item.get("user_info", {}).get("user_id", "N/A")
        for action_index in range(max_actions):
            current_batch_size = 0
            for task_item in task_data_list:
                user_info = task_item.get("user_info", {})
                user_info["udd"] = os.path.join(
                    self.udd_container_path, str(user_info.get("id"))
                )
                action_list = task_item.get("actions", [])
                if action_index < len(action_list):
                    action_info = action_list[action_index]

                    worker_item = {
                        "headless": headless,
                        "user_info": user_info,
                        "action_index": action_index,
                        "action_info": self.handle_action(user_info, action_info),
                    }
                    self._task_queue.put(worker_item)
                    current_batch_size += 1
                else:
                    # Service: User {user_id} has no action at index {action_index}. Skipping for this batch
                    pass
            if current_batch_size > 0:
                self._task_queue.join()
            else:
                pass

    def handle_action(self, user_info, action_info):
        user_type = user_info.get("type")
        action_name = action_info.get("action_name")
        if action_name == "launch":
            return {
                "action_name": action_name,
            }
        elif action_name == "discussion":
            post_info = action_info.get("post_info")
            if post_info == "random":
                # check in user_prev_discussion
                # handle option_id with type
                # get in data with option_id
                title = ""
                description = ""
                images = []
                pass
            elif post_info.get("pid"):
                # get in data with pid
                title = ""
                description = ""
                images = []
            else:
                title = post_info.get("title")
                description = post_info.get("description")
                images = post_info.get("images")

            return {
                "action_name": action_name,
                "post_info": {
                    "title": title,
                    "description": description,
                    "images": images,
                },
                "groups": action_info.get("groups", []),
            }

        elif action_name == "marketplace":
            pass
        elif action_name == "interaction":
            pass
        elif action_name == "group":
            pass

    @pyqtSlot(int, str, QObject)
    def _handle_worker_status(self, user_id: int, message: str, worker: QObject):
        print(f"User {user_id} (Worker {worker}): Status - {message}")
        self.task_status_update.emit(user_id, message)

    @pyqtSlot(int, str, QObject)
    def _handle_worker_error(self, user_id: int, error_message: str, worker: QObject):
        print(f"User {user_id} (Worker {worker}): ERROR - {error_message}")
        self.task_error_signal.emit(user_id, error_message)

    @pyqtSlot(int, QObject)
    def _handle_task_completed(self, user_id: int, worker: QObject):
        print(f"User {user_id} (Worker {worker}): One task completed successfully.")
        self.task_finished_signal.emit(user_id)

    @pyqtSlot(QObject)
    def _handle_worker_finished(self, worker: QObject):
        print(f"UserAutomationService: Worker {worker} thread finished.")
        if worker in self._running_automation_workers:
            thread_obj = self._running_automation_workers.pop(worker)
            print(
                f"Worker {worker}: Removed from tracking. Thread {thread_obj} exiting."
            )
            if not self._running_automation_workers:
                print(
                    "UserAutomationService: All workers have finished processing tasks and exited."
                )
                self.all_tasks_completed.emit()
        else:
            print(
                f"UserAutomationService: Worker {worker}: Finished signal received, but worker not found in tracking dict."
            )

    @pyqtSlot()
    def stop_all_tasks(self):
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
                self._task_queue.task_done()
            except queue.Empty:
                pass

        for worker, thread in list(
            self._running_automation_workers.items()
        ):  # Lặp trên bản sao items
            if thread.isRunning():
                print(
                    f"UserAutomationService: Requesting interruption for worker {worker} (thread {thread})."
                )
                thread.requestInterruption()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.database.re_database import initialize_re_db
    from src.database.user_database import initialize_user_db

    app = QApplication([])
    initialize_user_db()
    initialize_re_db()
    service = UserAutomationService()
    service.handle_task(
        task_data_list=[
            {
                "user_info": {
                    "id": 7,
                    "type": "re.r",
                    "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
                },
                "actions": [{"action_name": "launch"}],
            },
            {
                "user_info": {
                    "id": 9,
                    "type": "misc.shampoo",
                    "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                },
                "actions": [{"action_name": "launch"}],
            },
        ],
        headless=False,
    )

    sys.exit(app.exec())
