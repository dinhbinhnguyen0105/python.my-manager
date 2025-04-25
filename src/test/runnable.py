import sys
import time
import traceback
from collections import deque
from typing import Any, Dict, List, Tuple

from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot, Qt


class WorkerSignals(QObject):
    # signal cho Worker
    pass


class Worker(QRunnable):
    def __init__(self, job_data, source):
        super(Worker, self).__init__()
        # task_data dữ liệu cho công việc (task data)
        # resource tài nguyên được cấp phát (proxy)
        # signals
        self.autoDelete(True)

    @pyqtSlot()
    def run(self):
        try:
            # signals.status
            # TODO something
            pass
        except Exception as e:
            # signals.error
            # TODO exeception
            pass
        finally:
            # signals.finished
            pass
