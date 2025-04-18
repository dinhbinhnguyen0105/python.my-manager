from PyQt6.QtCore import QThread, QObject, pyqtSignal, QMutex


class Worker_CheckStatus(QObject):
    signal_progress = pyqtSignal(int)
    signal_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        self._mutex = QMutex()

    def run(self):

        pass

    def stop(self):
        self._mutex.lock()
        self._is_running = False
        self._mutex.unlock()
