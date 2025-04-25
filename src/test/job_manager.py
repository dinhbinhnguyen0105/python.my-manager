import sys
import time
import traceback
from collections import deque
from typing import Any, Dict, List, Tuple

from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot, Qt

class JobManager(QObject): #Service
        # Tín hiệu của Manager để báo cáo trạng thái tổng thể về GUI
    def __init__(self, resources, max_retries):
        super(JobManager, self).__init__()
        # Hàng đợi tài nguyên rảnh
        # Hàng đợi công việc chờ (chứa (job_data, retry_count))
        # Dict: resource -> (job_data, worker_instance)
        # Tổng số công việc ban đầu được thêm vào

        pass
    @pyqtSlot()
    def add_jobs(self, list_job_data):
        # Thêm một danh sách công việc mới vào hàng đợi chờ.
