# src/services/user_automation_service.py

import logging, sys, os
import queue # <-- Import thư viện Queue

from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt, pyqtSlot 

# Import lớp Worker
from src.automation.browser_worker import BrowserWorker 

# Import các Service Dữ liệu
from src.services.user_service import UserService       
from src.services.user_udd_service import UserUDDService 
from src.services.user_proxy_service import UserProxyService 

# get_proxy_pycurl không cần import ở đây nữa, nó dùng trong Worker


logger = logging.getLogger(__name__)
# Cấu hình logger
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - "%(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
# Set level INFO để thấy log tiến trình Service
logger.setLevel(logging.INFO) 


# Lớp UserAutomationService (Quản lý Pool Thread và các Hàng đợi)
class UserAutomationService(QObject):
    # Tín hiệu báo cáo trạng thái/hoàn thành/lỗi lên Controller
    task_status_update = pyqtSignal(int, str) 
    task_finished_signal = pyqtSignal(int) # Signal phát khi MỘT tác vụ cho user_id cụ thể hoàn thành
    task_error_signal = pyqtSignal(int, str) 
    
    # Thêm signal để báo khi TẤT CẢ tác vụ đã xử lý xong
    all_tasks_completed = pyqtSignal() 

    # Constructor (Nhận các Service Dữ liệu thông qua dependency injection)
    def __init__(
        self,
        user_service: UserService,
        udd_service: UserUDDService,
        proxy_service: UserProxyService,
        parent: QObject = None,
    ):
        super().__init__(parent)
        
        self._user_service = user_service
        self._udd_service = udd_service
        self._proxy_service = proxy_service
        
        # Dictionary để quản lý các worker đang chạy {worker_object: thread_object}
        self._running_automation_workers = {} 

        # --- Hàng đợi Nguồn Proxy Thô (dùng chung bởi các worker) ---
        self._proxy_source_queue = queue.Queue() 
        
        # --- Hàng đợi Tác vụ (chứa task_data cho từng record_id) ---
        self._task_queue = queue.Queue()

        # Số lượng worker/thread tối đa trong pool
        self._max_threads = 4 # <-- Đặt số lượng thread cố định, có thể cấu hình


        logger.info("UserAutomationService instance created.")

        # --- Tạo pool worker ngay khi Service được khởi tạo ---
        # Các worker này sẽ khởi động và chờ tác vụ trong _task_queue
        self._create_worker_pool(self._max_threads)


    # Phương thức khởi tạo pool worker
    def _create_worker_pool(self, num_workers):
         logger.info(f"Creating a pool of {num_workers} workers.")
         
         # Chỉ tạo worker nếu pool đang rỗng hoặc có ít worker hơn số lượng mong muốn
         current_worker_count = len(self._running_automation_workers)
         workers_to_add = num_workers - current_worker_count
         
         if workers_to_add <= 0:
             logger.info("Worker pool already has enough workers.")
             return # Không cần tạo thêm

         logger.info(f"Adding {workers_to_add} new workers to the pool.")

         for i in range(workers_to_add):
            thread = QThread()
            
            # === Tạo Worker VÀ TRUYỀN CẢ HAI HÀNG ĐỢI ===
            worker = BrowserWorker(task_queue=self._task_queue, proxy_queue=self._proxy_source_queue) 

            # Di chuyển worker sang luồng mới
            worker.moveToThread(thread)

            # --- Kết nối tín hiệu từ worker về Service (chạy trong luồng chính) ---
            # signal_status/error bây giờ sẽ báo cáo user_id của tác vụ hiện tại worker đang xử lý
            # signal_finished sẽ báo hiệu worker THOÁT VÒNG LẶP chính (hoàn thành tất cả tác vụ hoặc bị dừng)
            
            # Truyền worker object với tín hiệu để Service biết worker nào báo cáo
            worker.signal_status.connect(lambda user_id, msg, w=worker: self._handle_worker_status(w, user_id, msg))
            worker.signal_error.connect(lambda user_id, msg, w=worker: self._handle_worker_error(w, user_id, msg))
            
            # Tín hiệu finished của worker chỉ phát khi worker THOÁT VÒNG LẶP CHÍNH (hết tác vụ/bị dừng)
            worker.signal_finished.connect(lambda w=worker: self._handle_worker_finished(w)) 

            # --- Kết nối tín hiệu finished của thread để dọn dẹp Worker và Thread ---
            # Các slot deleteLater an toàn để gọi nhiều lần
            thread.finished.connect(worker.deleteLater) 
            thread.finished.connect(thread.deleteLater) 

            # --- Kết nối tín hiệu started của thread tới phương thức chạy công việc trong Worker ---
            # Worker sẽ chạy vòng lặp trong run_browser_task để lấy tác vụ từ hàng đợi
            thread.started.connect(worker.run_browser_task) 

            # --- Bắt đầu luồng ---
            thread.start()
            # print(f"UserAutomationService: Started thread {thread} for worker {worker}.") # Log chi tiết thread/worker object
            logger.info(f"UserAutomationService: Started thread for worker {worker}.") 

            # --- Lưu trữ Worker và Thread trong dictionary quản lý pool ---
            # Sử dụng worker object làm key
            self._running_automation_workers[worker] = thread 

         logger.info(f"UserAutomationService: Worker pool created/updated. Pool size: {len(self._running_automation_workers)}")


    # Phương thức này được Controller gọi để bắt đầu xử lý một tập hợp record_ids
    @pyqtSlot(list, bool) 
    def launch_automation_tasks(self, record_ids: list, is_mobile: bool = False):
        print(f"UserAutomationService: Received launch request for IDs: {record_ids}")
        logger.info(f"UserAutomationService: Launching automation tasks for IDs: {record_ids}")

        # --- 1. Thu thập dữ liệu cần thiết chung ---
        udd_container_data = self._udd_service.get_selected_udd() 
        if not udd_container_data or 'value' not in udd_container_data:
            logger.error("UserAutomationService: cannot get user data dir container path")
            self.task_error_signal.emit(-1, "Cannot get UDD container path.") 
            # self.task_finished_signal.emit(-1) # Không phát finished cho lỗi chung
            return False
        udd_container_path = udd_container_data.get('value')

        proxy_records = self._proxy_service.read_all() 
        proxy_sources = [proxy_record.get("value") for proxy_record in proxy_records if proxy_record and "value" in proxy_record]

        if not proxy_sources:
            logger.warning("UserAutomationService: No proxy records found. All tasks will run without proxies.")

        # --- 2. Đổ các nguồn proxy thô vào Hàng đợi Nguồn Proxy (cho Worker lấy) ---
        # Bạn có thể quyết định làm rỗng hàng đợi cũ hoặc thêm vào
        # Nếu muốn pool proxy mới mỗi lần launch:
        # self._proxy_source_queue = queue.Queue() 
        while not self._proxy_source_queue.empty(): # Xóa proxy cũ nếu muốn pool mới
             try: self._proxy_source_queue.get_nowait()
             except queue.Empty: pass # Tránh lỗi khi queue rỗng
        
        for source in proxy_sources:
            self._proxy_source_queue.put(source)
        logger.info(f"UserAutomationService: Reloaded {len(proxy_sources)} raw proxy sources into the proxy queue.")


        # --- 3. Đổ các Tác vụ (task_data) vào Hàng đợi Tác vụ ---
        # Tạo hàng đợi tác vụ mới cho tập hợp ID này
        # self._task_queue = queue.Queue() # Nếu muốn hàng đợi tác vụ mới mỗi lần launch
        
        # Kiểm tra các task_id đã tồn tại trong queue hiện tại (nếu không tạo queue mới mỗi lần)
        # Nếu bạn tạo queue mới mỗi lần launch, không cần check này
        existing_task_ids_in_queue = [] # Cần duyệt queue để kiểm tra, phức tạp. 
                                        # Đơn giản là thêm vào hoặc tạo queue mới.

        initial_task_count = self._task_queue.qsize()
        
        for record_id in record_ids:
            # Kiểm tra xem tác vụ cho user này đã chạy chưa (bằng dictionary worker quản lý)
            # Việc kiểm tra này phức tạp hơn với pool. 
            # Worker có thể đang xử lý task cho user đó. 
            # Hoặc user_id đó có trong queue nhưng chưa được xử lý.
            # Cách đơn giản nhất là không kiểm tra "Already running" ở đây cho pool worker.
            # Để worker tự xử lý nếu task_data cho user đó có vấn đề (ví dụ: user deleted).
            
            # Lấy thông tin cụ thể cho user
            user_data = self._user_service.read(record_id) 
            if not user_data:
                logger.warning(f"User {record_id}: User data not found, skipping queueing task.")
                self.task_error_signal.emit(record_id, "User data not found") # Báo lỗi user cụ thể
                continue 

            ua = self._user_service.get_ua(record_id, is_mobile) 
            if not ua:
                 logger.warning(f"User {record_id}: User Agent not available, skipping queueing task.")
                 self.task_error_signal.emit(record_id, "User Agent not available") # Báo lỗi user cụ thể
                 continue

            udd_path_for_user = os.path.abspath(os.path.join(udd_container_path, str(record_id))) 
            
            # === Tạo dictionary task_data cho user này ===
            task_data = {
                'user_id': record_id, 
                'user_data_dir': udd_path_for_user, 
                'user_agent': ua,
                'headless': is_mobile, # Lấy cờ headless
                
                # Hàng đợi proxy KHÔNG ĐẶT Ở ĐÂY. Nó được truyền vào Worker __init__.
                # Các thông tin user khác cần cho tác vụ
                'target_url': "https://whatismyipaddress.com/", 
                'username': user_data.get('username'), 
                'password': user_data.get('password'),
                'two_fa': user_data.get('two_fa'),
            }

            # --- Đưa task_data vào hàng đợi tác vụ ---
            self._task_queue.put(task_data)
            logger.debug(f"User {record_id}: Task queued.")

        final_task_count = self._task_queue.qsize()
        added_tasks = final_task_count - initial_task_count
        logger.info(f"UserAutomationService: Queued {added_tasks} new tasks. Total tasks in queue: {final_task_count}.")

        # === Các worker trong pool sẽ tự động bắt đầu xử lý các tác vụ mới trong hàng đợi ===
        # Không cần lặp qua record_ids để start thread ở đây nữa


    # --- Các Slot xử lý tín hiệu từ Worker (Chạy trong luồng chính - GUI Thread) ---
    # Các slot này nhận tín hiệu từ Worker và phát tín hiệu của Service lên Controller
    # Worker cần phát user_id và thông tin cần thiết
    # Worker cần phát worker object (self) với signal_finished

    # Signal status và error nên truyền user_id của task hiện tại mà worker đang làm
    # Signal status: signal_status = pyqtSignal(int, str) -> worker.signal_status.emit(user_id_hien_tai, msg)
    # Signal error: signal_error = pyqtSignal(int, str) -> worker.signal_error.emit(user_id_cua_task_loi, msg_loi)
    # Service slots nhận user_id và msg
    @pyqtSlot(int, str) 
    def _handle_worker_status(self, user_id: int, message: str):
        # Log này sẽ báo cáo user_id của task mà worker đang xử lý
        logger.debug(f"User {user_id}: Status - {message}")
        # Phát tín hiệu lên Controller/View
        self.task_status_update.emit(user_id, message)

    @pyqtSlot(int, str) 
    def _handle_worker_error(self, user_id: int, error_message: str):
        # Log này sẽ báo cáo user_id của task gặp lỗi
        logger.error(f"UserAutomationService: Worker error for User {user_id}: {error_message}")
        # Phát tín hiệu lên Controller/View
        self.task_error_signal.emit(user_id, error_message)
        # Controller/View có thể cập nhật trạng thái cho user_id này là lỗi

    # === Slot xử lý tín hiệu finished của Worker ===
    # Tín hiệu finished của worker chỉ phát khi worker THOÁT VÒNG LẶP CHÍNH trong run_browser_task
    # Điều này xảy ra khi hàng đợi tác vụ rỗng và không còn gì để làm, hoặc worker bị yêu cầu dừng
    # Worker phát tín hiệu finished và truyền chính nó (self)
    @pyqtSlot(QObject) # Slot nhận worker object
    def _handle_worker_finished(self, worker: QObject):
        logger.info(f"UserAutomationService: Worker {worker} thread finished.")
        
        # Xóa worker khỏi dictionary quản lý pool
        if worker in self._running_automation_workers:
            thread_obj = self._running_automation_workers.pop(worker) 
            # print(f"UserAutomationService: Removed worker {worker} (thread {thread_obj}) from tracking.")
            logger.debug(f"Worker {worker}: Removed from tracking.")
            
            # --- Kiểm tra xem tất cả worker đã kết thúc chưa ---
            if not self._running_automation_workers:
                logger.info("UserAutomationService: All workers have finished processing tasks.")
                # === Phát tín hiệu báo TẤT CẢ tác vụ đã hoàn thành ===
                self.all_tasks_completed.emit() 
                logger.info("UserAutomationService: Emitted all_tasks_completed signal.")

        else:
             logger.warning(f"UserAutomationService: Worker {worker}: Finished signal received, but worker not found in tracking dict.")

        # task_finished_signal (cho TỪNG user_id) sẽ được worker phát ra BÊN TRONG vòng lặp xử lý task


    # --- Phương thức Dừng Tất cả các Tác vụ Đang chạy ---
    # Phương thức này được Controller gọi khi cần dừng pool worker
    @pyqtSlot() 
    def stop_all_automation_tasks(self):
        logger.info("UserAutomationService: Requesting all workers to stop.")
        
        # Rỗng hàng đợi tác vụ ngay lập tức (tùy chọn)
        while not self._task_queue.empty():
            try: 
                # Lấy các item ra khỏi queue nhưng không xử lý
                self._task_queue.get_nowait() 
                # Cần gọi task_done cho các item bị bỏ qua này nếu dùng JoinableQueue
                # self._task_queue.task_done() # Bỏ ghi chú nếu dùng JoinableQueue
            except queue.Empty: 
                pass # Tránh lỗi nếu queue đã rỗng

        # Yêu cầu tất cả các worker đang chạy ngắt (worker cần kiểm tra cờ này)
        for worker, thread in self._running_automation_workers.items(): 
            if thread.isRunning():
                 logger.info(f"UserAutomationService: Requesting interruption for worker {worker} (thread {thread}).")
                 thread.requestInterruption() # Worker cần kiểm tra cờ này trong vòng lặp và các thao tác chặn

        # Bạn có thể muốn chờ các worker kết thúc ở đây nếu cần đảm bảo chúng dừng hoàn toàn
        # trước khi hàm stop_all này trả về (ví dụ khi đóng ứng dụng)
        # for worker, thread in list(self._running_automation_workers.items()): # Lặp trên bản sao
        #     if thread.isRunning():
        #          logger.info(f"UserAutomationService: Waiting for worker {worker} thread to finish.")
        #          thread.wait(5000) # Chờ tối đa 5 giây
        #          if thread.isRunning():
        #              logger.warning(f"Worker {worker}: Thread did not finish gracefully after waiting.")


# --- Cần đảm bảo các Service dữ liệu (UserService, UDD, Proxy) được inject khi tạo UserAutomationService ---
# Ví dụ trong MainWindow:
# user_service = UserService()
# udd_service = UserUDDService()
# proxy_service = UserProxyService()
# automation_service = UserAutomationService(user_service, udd_service, proxy_service)