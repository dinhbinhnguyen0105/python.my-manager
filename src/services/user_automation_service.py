# src/services/user_automation_service.py
import sys, logging, os
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import queue

from src.services.user_service import UserService, UserUDDService, UserProxyService
from src.models.worker_launch_browser import LaunchBrowser_Worker


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


class UserAutomationService(QObject):
    task_status_update = pyqtSignal(int, str)
    task_finished_signal = pyqtSignal(int)
    task_error_signal = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user_service = UserService()
        self._udd_service = UserUDDService()
        self._proxy_service = UserProxyService()
        self._running_automation_tasks = {}
        self._proxy_source_queue = queue.Queue()

    @pyqtSlot(list, bool)
    def launch_automation_task(self, record_ids: list, is_mobile: bool = False):
        udd_container_dir = self._udd_service.get_selected_udd()
        if not udd_container_dir:
            logger.error(
                "UserAutomationService: cannot get user data dir container path"
            )
            self.task_error_signal.emit(-1, "Cannot get UDD container path")
            self.task_finished_signal.emit(-1)
            return False
        proxy_records = self._proxy_service.read_all()
        proxy_sources = [
            proxy_record.get("value")
            for proxy_record in proxy_records
            if proxy_record and "value" in proxy_record
        ]
        if not proxy_sources:
            logger.error("UserAutomationService: No proxy records found.")
            self.task_error_signal.emit(-1, "No proxies available.")
            self.task_finished_signal.emit(-1)
            return False
        for source in proxy_sources:
            self._proxy_source_queue.put(source)

        for record_id in record_ids:
            if (
                record_id in self._running_automation_tasks
                and self._running_automation_tasks[record_id][
                    "thread"
                ].isRunning()  # ERROR
            ):
                self.task_status_update.emit(record_id, "Already running")
                continue
            ua = self._user_service.get_ua(record_id, is_mobile=is_mobile)
            if not ua:
                logger.error(
                    f"UserAutomationService: User Agent not found for User ID {record_id}, skipping task launch."
                )
                self.task_error_signal.emit(record_id, "User Agent not available")
                self.task_finished_signal.emit(record_id)
                continue
            udd = os.path.abspath(os.path.join(udd_container_dir, str(record_id)))
            task_data = {
                "user_id": record_id,
                "udd": udd,
                "proxy_queue": self._proxy_source_queue,
                "ua": ua,
                "headless": False,
            }
            thread = QThread()
            worker = LaunchBrowser_Worker(task_data)
            worker.moveToThread(thread)
            worker.signal_status.connect(
                lambda msg, user_id=record_id: self._handle_worker_status(user_id, msg)
            )
            worker.signal_finished.connect(
                lambda user_id=record_id: self._handle_worker_finished(user_id)
            )
            worker.signal_error.connect(
                lambda msg, user_id=record_id: self._handle_worker_error(user_id, msg)
            )

            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            worker.signal_finished.connect(thread.quit)

            thread.started.connect(worker.do_work)
            self._running_automation_tasks[record_id] = {
                "thread": thread,
                "worker": worker,
            }

            print("Preparing ...")
            thread.start()

            self.task_status_update.emit(record_id, "Launching ...")

    @pyqtSlot(int, str)
    def _handle_worker_status(self, user_id: int, msg: str):  # Xử lý signal của worker
        logger.info(f"User id '{user_id}' progress: {msg}")

    @pyqtSlot(int)
    def _handle_worker_finished(self, user_id: int):
        logger.info(f"User id '{user_id}': Finished.")
        if user_id in self._running_automation_tasks:
            thread = self._running_automation_tasks[user_id]["thread"]
            thread.quit()
            thread.wait()  # Đảm bảo luồng đã kết thúc
            del self._running_automation_tasks[user_id]
            logger.debug(f"User {user_id}: Removed task from tracking.")

    @pyqtSlot(int, str)
    def _handle_worker_error(self, user_id: int, msg: str):
        logger.info(f"User id'{user_id}' error: {msg}")
        pass

    @pyqtSlot()
    def stop_all_automation_task(self):
        for user_id, thread in list(self._running_automation_tasks.items()):
            if thread.isRunning():
                thread.requestInterruption()
