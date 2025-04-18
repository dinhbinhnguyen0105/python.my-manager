from PyQt6.QtCore import QThread, QObject, pyqtSignal, QMutex, Qt

from src.robot.selenium_controller import SeleniumController
import undetected_chromedriver as uc


class Worker(QObject):
    signal_process = pyqtSignal(int)
    signal_finished = pyqtSignal(int)

    def __init__(self, worker_id, udd, proxy, ua, parent=None):
        super().__init__(parent)
        self.worker_id = worker_id
        self._isRunning = True
        self._mutex = QMutex()

        self.udd = udd
        self.proxy = proxy
        self.ua = ua

    def do_work(self):
        controller = SeleniumController(
            {
                "udd": self.udd,
                "proxy": self.ua,
                "ua": self.ua,
            }
        )
        controller.init_driver()

        self.signal_finished.emit(self.worker_id)


# for i in range(total_steps + 1):
#     self._mutex.lock()
#     if not self._isRunning:
#         self._mutex.unlock()
#         print(f"Worker {self.worker_id}: Công việc bị hủy.")
#         break
#     self._mutex.unlock()

#     # Giả lập công việc tốn thời gian
#     time.sleep(sleep_duration)

#     # Phát tín hiệu báo cáo tiến độ (bao gồm ID worker)
#     self.signal_progress.emit(self.worker_id, int((i / total_steps) * 100))
