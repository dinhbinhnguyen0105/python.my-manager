# src/automation/browser_worker.py

import logging # Đảm bảo logger đã cấu hình ở đây và level phù hợp (INFO/DEBUG)
import sys
import os 
import time 
import random 
import queue # <-- Import thư viện Queue

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import BrowserContext, Page 
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError 

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QCoreApplication # Import QCoreApplication

from urllib.parse import urlparse 
# Import hàm PycURL check proxy - Đảm bảo đường dẫn import đúng
# from src.utils.proxy_utils import get_proxy_pycurl 
from src.utils.user_handler import get_proxy_pycurl 

# Cấu hình logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - "%(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
logger.setLevel(logging.INFO) # Set level INFO/DEBUG để thấy log chi tiết trong Worker


# Lớp Worker sẽ chạy trong QThread và xử lý nhiều tác vụ từ hàng đợi
class BrowserWorker(QObject): 
    # Tín hiệu báo cáo trạng thái/lỗi cho MỘT tác vụ cụ thể (kèm user_id)
    # Thêm worker object (self) vào tín hiệu để Service biết worker nào báo cáo
    signal_status = pyqtSignal(int, str, QObject) # user_id, message, worker_self
    signal_error = pyqtSignal(int, str, QObject)  # user_id, message, worker_self
    # Tín hiệu phát khi MỘT TÁC VỤ (cho user_id) hoàn thành thành công
    task_completed_signal = pyqtSignal(int, QObject) # user_id, worker_self 

    # Tín hiệu báo worker THOÁT VÒNG LẶP chính (hoàn thành hết tác vụ hoặc bị dừng)
    # Tín hiệu này được kết nối tới thread.quit() trong Service
    signal_finished = pyqtSignal(QObject) # Phát chính worker object (self)

    # Constructor nhận cả hai hàng đợi
    def __init__(
        self, 
        task_queue: queue.Queue,      # Hàng đợi tác vụ (task_data dicts)
        proxy_queue: queue.Queue | None, # Hàng đợi nguồn proxy thô (có thể là None)
        parent: QObject = None
    ): 
        super().__init__(parent)
        
        self._task_queue = task_queue # Lưu instance hàng đợi tác vụ
        self._proxy_queue = proxy_queue # Lưu instance hàng đợi proxy

        # --- Thuộc tính sẽ được cập nhật cho MỖI TÁC VỤ được lấy từ hàng đợi ---
        self.user_id = -1 
        self.udd_path = None
        self.user_agent = None
        self.headless = False
        self.target_url = None
        self.username = None
        self.password = None
        self.two_fa = None
        self.playwright_proxy_config = None # Proxy cho tác vụ HIỆN TẠI


        logger.debug(f"Worker {self} initialized, ready to process tasks.")


    # Hàm parse proxy string (có thể bỏ nếu get_proxy_pycurl trả về dict)
    # def _parse_proxy_string_for_playwright(self, proxy_string: str | None) -> dict | None: ...


    # --- Phương thức chính chạy trong luồng phụ ---
    @pyqtSlot() 
    def run_browser_task(self):
        logger.info(f"Worker thread {self.thread()} ({self}) started.")
        
        # --- Main loop để xử lý các tác vụ từ hàng đợi ---
        # Vòng lặp này chạy cho đến khi worker được yêu cầu dừng HOẶC hàng đợi tác vụ rỗng
        while True:
             # --- Kiểm tra yêu cầu ngắt từ luồng chính (Service.stop_all_...) ---
             # QThread.isInterruptionRequested() kiểm tra cờ ngắt
             # QCoreApplication.processEvents() cho phép xử lý các sự kiện (bao gồm yêu cầu ngắt) 
             # khi worker đang bận không block (ví dụ: giữa các thao tác Playwright)
             # hoặc trong timeout của queue.get
             
             if self.thread() and self.thread().isInterruptionRequested():
                  logger.info(f"Worker thread {self.thread()}: Interruption requested. Exiting task loop.")
                  break # Thoát khỏi vòng lặp chính

             # --- 1. Lấy dữ liệu tác vụ tiếp theo từ Hàng đợi Tác vụ ---
             # Worker sẽ chờ tại đây cho đến khi có tác vụ HOẶC hết timeout
             try:
                  logger.info(f"Worker thread {self.thread()}: Waiting for next task...")
                  # Lấy task_data. Block cho đến khi available, hoặc timeout.
                  # Dùng timeout (ví dụ 1000ms = 1s) để worker không block vô hạn và có thể kiểm tra cờ ngắt
                  task_data = self._task_queue.get(block=True, timeout=1000) 

                  # --- Cập nhật thuộc tính của worker cho TÁC VỤ MỚI này ---
                  # worker sẽ làm việc với dữ liệu của user trong task_data này
                  self.user_id = task_data.get('user_id', -1)
                  self.udd_path = task_data.get('user_data_dir')
                  self.user_agent = task_data.get('user_agent')
                  self.headless = task_data.get('headless', False)
                  self.target_url = task_data.get('target_url', 'https://whatismyipaddress.com/')
                  self.username = task_data.get('username')
                  self.password = task_data.get('password')
                  self.two_fa = task_data.get('two_fa')
                  
                  # Reset proxy config cho tác vụ MỚI
                  self.playwright_proxy_config = None 

                  logger.info(f"Worker thread {self.thread()}: Got task for User ID {self.user_id}.")
                  # Báo trạng thái cho tác vụ hiện tại
                  self.signal_status.emit(self.user_id, f"User {self.user_id}: Task received.", self)


             except queue.Empty:
                  # Hàng đợi tác vụ rỗng sau khi chờ timeout.
                  # Nếu không có yêu cầu ngắt, worker có thể thoát nếu không còn gì để làm.
                  # Hoặc tiếp tục chờ nếu kỳ vọng có tác vụ mới được thêm vào sau.
                  # Với pool cố định, worker nên thoát khi queue rỗng.
                  logger.info(f"Worker thread {self.thread()}: Task queue is empty. Exiting task loop.")
                  break # Thoát khỏi vòng lặp chính khi hết tác vụ

             except Exception as e:
                  # Xử lý lỗi không mong muốn khi lấy tác vụ từ hàng đợi
                  # Lỗi này nghiêm trọng, có thể break vòng lặp hoặc log và tiếp tục
                  logger.error(f"Worker thread {self.thread()}: Error getting task from queue: {e}", exc_info=True)
                  # Báo lỗi cho user_id hiện tại (hoặc user_id trước đó nếu chưa kịp cập nhật)
                  self.signal_error.emit(self.user_id, f"Error getting task from queue: {e}", self)
                  # Decide: break or continue? Let's continue to try next task for robustness.
                  continue 


             # --- Check for interruption request AFTER getting task ---
             if self.thread() and self.thread().isInterruptionRequested():
                  logger.info(f"Worker thread {self.thread()}: Interruption requested after getting task {self.user_id}. Aborting task.")
                  self.signal_status.emit(self.user_id, f"User {self.user_id}: Interrupted.", self)
                  # Mark task as done in queue even if aborted
                  self._task_queue.task_done() 
                  logger.info(f"Worker thread {self.thread()}: Task {self.user_id} marked as done in queue (aborted).")
                  break # Thoát khỏi vòng lặp chính


             # --- 2. Lấy proxy từ Hàng đợi Nguồn Proxy cho TÁC VỤ HIỆN TẠI này ---
             # Logic này chạy cho MỖI tác vụ được lấy từ hàng đợi tác vụ
             raw_proxy_source = None
             self.playwright_proxy_config = None # Đảm bảo reset proxy config cho tác vụ mới
             max_get_proxy_attempts = 5 # Số lần thử lấy proxy cho MỘT tác vụ

             if self._proxy_queue: # Chỉ thực hiện nếu có hàng đợi proxy
                 logger.info(f"Worker thread {self.thread()}: Getting proxy for task {self.user_id}.")
                 # Vòng lặp thử lấy proxy từ _proxy_queue bằng get_proxy_pycurl
                 for attempt in range(1, max_get_proxy_attempts + 1):
                      # === KIỂM TRA NGẮT TRONG VÒNG LẶP LẤY PROXY ===
                      if self.thread() and self.thread().isInterruptionRequested():
                           logger.info(f"Worker thread {self.thread()}: Interruption requested during proxy fetching for {self.user_id}. Aborting task.")
                           self.signal_status.emit(self.user_id, f"User {self.user_id}: Interrupted.", self)
                           # Mark task as done in queue (aborted)
                           self._task_queue.task_done()
                           logger.info(f"Worker thread {self.thread()}: Task {self.user_id} marked as done in queue (aborted during proxy fetch).")
                           return # Thoát toàn bộ run_browser_task (và vòng lặp chính)

                      try:
                          # Lấy nguồn proxy thô từ hàng đợi proxy. Block cho đến khi có hoặc hết timeout.
                          # Dùng timeout để có thể kiểm tra cờ ngắt
                          raw_proxy_source = self._proxy_queue.get(block=True, timeout=5000) # Timeout 5 giây

                          logger.debug(f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - Got raw proxy source: {raw_proxy_source}")

                          # === Gọi hàm get_proxy_pycurl (hàm fetch và check proxy) ===
                          # Hàm này làm việc nặng (I/O mạng), chạy trong luồng worker
                          processed_proxy_dict = get_proxy_pycurl(raw_proxy_source) 

                          if processed_proxy_dict:
                              # Thành công! Lưu cấu hình proxy cho Playwright và thoát vòng lặp thử
                              self.playwright_proxy_config = processed_proxy_dict
                              logger.info(f"User {self.user_id}: Successfully obtained and checked proxy on attempt {attempt}.")
                              self.signal_status.emit(self.user_id, f"User {self.user_id}: Proxy obtained.", self)
                              self._proxy_queue.task_done() # Báo hiệu nguồn proxy này đã xử lý xong (dù check OK hay Fail)
                              break # Thoát vòng lặp thử lấy proxy cho tác vụ hiện tại

                          else:
                              # get_proxy_pycurl trả về False (proxy test failed hoặc parse lỗi API)
                              logger.warning(f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - get_proxy_pycurl failed for {raw_proxy_source}.")
                              self.signal_status.emit(self.user_id, f"User {self.user_id}: Proxy failed check.", self)
                              self._proxy_queue.task_done() # Báo hiệu nguồn proxy này đã xử lý xong (dù check OK hay Fail)
                              # Quyết định: Có thử lại nguồn proxy này sau không? (Nếu lỗi tạm thời)
                              # Đơn giản là bỏ qua nguồn này và lấy nguồn tiếp theo trong lần thử tiếp theo (nếu còn attempts)

                      except queue.Empty:
                          # Hàng đợi nguồn proxy rỗng sau khi chờ timeout
                          logger.warning(f"User {self.user_id}: Proxy source queue is empty after waiting. Cannot get proxy for this task.")
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Proxy queue empty.", self)
                          # Không có proxy để thử tiếp cho tác vụ này
                          break # Thoát vòng lặp thử lấy proxy

                      except Exception as e:
                          # Lỗi xảy ra trong quá trình get_proxy_pycurl (ví dụ: API không phản hồi, lỗi mạng)
                          logger.error(f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - Error calling get_proxy_pycurl for {raw_proxy_source}: {e}", exc_info=True)
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Get proxy error.", self)
                          if raw_proxy_source is not None: 
                               self._proxy_queue.task_done() # Báo hiệu nguồn proxy này đã xử lý xong (với lỗi)
                          # Quyết định: Có thử lại nguồn proxy này sau không?
                          # self._proxy_queue.put(raw_proxy_source) # Nếu muốn thử lại nguồn này sau
                          # Đơn giản là bỏ qua nguồn này

                 # --- Kết thúc vòng lặp thử lấy proxy cho tác vụ hiện tại ---

                 if not self.playwright_proxy_config:
                     # Không tìm được proxy cho tác vụ hiện tại sau tất cả các lần thử
                     logger.warning(f"User {self.user_id}: Failed to obtain a valid proxy after {max_get_proxy_attempts} attempts for this task.")
                     self.signal_error.emit(self.user_id, f"User {self.user_id}: Failed to obtain proxy for task.", self)
                     self.signal_status.emit(self.user_id, f"User {self.user_id}: No proxy assigned for task.", self)
                     # Quyết định: Có bỏ qua tác vụ này nếu không có proxy không?
                     # Nếu proxy là bắt buộc:
                     # self.signal_status.emit(self.user_id, f"User {self.user_id}: Skipping (no proxy).", self)
                     # self.task_completed_signal.emit(self.user_id, self) # Coi như task hoàn thành với lỗi
                     # self._task_queue.task_done() # Đã gọi task_done ở trên
                     # continue # Bỏ qua tác vụ này và lấy tác vụ tiếp theo từ hàng đợi

             else:
                 logger.info(f"User {self.user_id}: Proxy source queue is not available, proceeding without proxy for task {self.user_id}.")
                 self.signal_status.emit(self.user_id, f"User {self.user_id}: No proxy queue.", self)
                 # playwright_proxy_config vẫn là None, browser sẽ chạy không proxy


             # --- 3. Execute Playwright Automation cho TÁC VỤ HIỆN TẠI ---
             # Logic này chạy cho MỖI tác vụ được lấy từ hàng đợi tác vụ (nếu không bị bỏ qua)
             try:
                 logger.info(f"Worker thread {self.thread()}: Running Playwright task for User {self.user_id}.")
                 self.signal_status.emit(self.user_id, f"User {self.user_id}: Running automation...", self)

                 # --- Launch Browser (sử dụng dữ liệu của tác vụ hiện tại) ---
                 with sync_playwright() as p:
                      # Xây dựng launch_options bằng các thuộc tính đã cập nhật cho tác vụ hiện tại
                      custom_browser_args = ["--disable-blink-features=AutomationControlled", "--disable-infobars", "--disable-extensions", '--no-sandbox']
                      launch_options = {
                          'user_data_dir': self.udd_path, 
                          'headless': self.headless, 
                          'args': custom_browser_args, 
                          'user_agent': self.user_agent,
                          # Sử dụng proxy_config đã lấy được cho tác vụ này
                          'proxy': self.playwright_proxy_config, # proxy_config là dictionary hoặc None
                      }
                      # Log trạng thái sử dụng proxy
                      if self.playwright_proxy_config: logger.debug(f"User {self.user_id}: Using proxy {self.playwright_proxy_config.get('server')} for automation.")
                      else: logger.debug(f"User {self.user_id}: Running automation without proxy.")


                      # Khởi chạy browser context (có thể lỗi khi launch nếu proxy không hoạt động tốt dù check ban đầu)
                      # Bắt lỗi cụ thể hơn nếu cần (ví dụ: PlaywrightError khi launch)
                      browser_context = p.chromium.launch_persistent_context(**launch_options)
                      logger.info(f"User {self.user_id}: Browser context launched for task {self.user_id}.")
                      self.signal_status.emit(self.user_id, f"User {self.user_id}: Browser ready.", self)

                      # Cấu hình Context (Init Scripts)
                      stealth_script = """ Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); """
                      try: browser_context.add_init_script(stealth_script)
                      except Exception as e: logger.warning(f"User {self.user_id}: Error adding init script: {e}")

                      # Tạo Page Mới
                      logger.info(f"User {self.user_id}: Creating new page for task {self.user_id}.")
                      page = browser_context.new_page()
                      logger.debug(f"User {self.user_id}: Page created.")
                      self.signal_status.emit(self.user_id, f"User {self.user_id}: Page ready.", self)

                      # --- Thực hiện Công việc Tự động hóa Chính cho TÁC VỤ NÀY ---
                      # Sử dụng các thuộc tính self đã cập nhật cho tác vụ hiện tại
                      logger.info(f"User {self.user_id}: Navigating to {self.target_url} for task.")
                      self.signal_status.emit(self.user_id, f"User {self.user_id}: Navigating...", self)

                      # Bọc logic thao tác browser trong try...except để bắt lỗi cụ thể cho thao tác này
                      try:
                          # Ví dụ: goto, fill, click, wait_for_selector, v.v.
                          # === KIỂM TRA NGẮT TRONG QUÁ TRÌNH THAO TÁC ===
                          if self.thread() and self.thread().isInterruptionRequested():
                               logger.info(f"User {self.user_id}: Interruption requested during Playwright task execution. Aborting.")
                               self.signal_status.emit(self.user_id, f"User {self.user_id}: Interrupted.", self)
                               raise InterruptedError("Task interrupted") # Ném lỗi để thoát khối try/except này

                          page.goto(self.target_url, timeout=60000) # Timeout 60s cho goto
                          logger.info(f"User {self.user_id}: Navigated to {self.target_url}.")
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Page loaded.", self)

                          # --- Thêm code tương tác khác tại đây ---
                          # time.sleep(random.uniform(5, 15)) # Ví dụ delay
                          # if self.thread() and self.thread().isInterruptionRequested(): raise InterruptedError # Kiểm tra ngắt giữa các thao tác


                          # === ĐIỂM DỪNG: CHỜ NGƯỜI DÙNG ĐÓNG TRANG HOẶC HẾT TIMEOUT ===
                          logger.info(f"User {self.user_id}: Waiting for page close or timeout...")
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Waiting for manual close...", self)
                          
                          # === SỬ DỤNG page.wait_for_event VỚI TIMEOUT > 0 HOẶC NONE ===
                          # Đặt timeout phù hợp (ví dụ 5 phút = 300000ms)
                          wait_timeout_ms = 300000 
                          try:
                               # wait_for_event cũng cần kiểm tra ngắt nếu timeout lớn
                               # Nhưng QThread.requestInterruption() không làm Playwright stop blocking wait_for_event
                               # Cần cách riêng để dừng wait_for_event từ ngoài luồng nếu timeout lớn
                               # Tạm thời chấp nhận nó block cho đến hết timeout hoặc đóng page
                               page.wait_for_event("close", timeout=wait_timeout_ms) 
                               logger.info(f"User {self.user_id}: Page closed manually.")
                               self.signal_status.emit(self.user_id, f"User {self.user_id}: Page closed.", self)
                          except PlaywrightTimeoutError:
                               logger.warning(f"User {self.user_id}: Wait for page close timed out after {wait_timeout_ms/1000}s.")
                               self.signal_status.emit(self.user_id, f"User {self.user_id}: Wait timeout.", self)
                               # Browser vẫn mở sau timeout

                          # === KẾT THÚC ĐIỂM DỪNG ===

                          logger.info(f"User {self.user_id}: Automation task logic completed for User {self.user_id}.")
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Task logic done.", self)

                          # === Báo hiệu MỘT TÁC VỤ (cho user_id này) hoàn thành thành công ===
                          self.task_completed_signal.emit(self.user_id, self)
                          logger.debug(f"User {self.user_id}: Emitted task_completed_signal.")


                      # --- Bắt lỗi riêng cho các thao tác browser trong task logic ---
                      except InterruptedError:
                           # Đã xử lý ngắt
                           logger.info(f"User {self.user_id}: Task {self.user_id} aborted due to interruption.")
                           self.signal_status.emit(self.user_id, f"User {self.user_id}: Aborted.", self)
                           # Không cần emit error, đã là interrupted

                      except PlaywrightTimeoutError as task_timeout_error:
                           # Lỗi Timeout cho goto, wait_for_selector, v.v.
                          logger.error(f"User {self.user_id}: Task timeout error for {self.user_id}: {task_timeout_error}", exc_info=True)
                          self.signal_error.emit(self.user_id, f"User {self.user_id}: Task Timeout.", self)
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Task Timeout.", self)

                      except Exception as page_interaction_error:
                           # Bắt các lỗi chung khác trong quá trình thao tác trên page
                          logger.error(f"User {self.user_id}: Error during page interaction for {self.user_id}: {page_interaction_error}", exc_info=True)
                          self.signal_error.emit(self.user_id, f"User {self.user_id}: Automation Error: {page_interaction_error}", self)
                          self.signal_status.emit(self.user_id, f"User {self.user_id}: Automation Error.", self)

                      # --- Kết thúc khối try...except cho logic thao tác browser ---


                 # --- Dọn dẹp tài nguyên Playwright cho tác vụ hiện tại ---
                 # Code này chạy sau khi khối try/except cho logic thao tác browser kết thúc
                 logger.info(f"User {self.user_id}: Attempting resource cleanup for task.")
                 self.signal_status.emit(self.user_id, f"User {self.user_id}: Cleaning up task.", self)
                 
                 if page: 
                      try: 
                          if not page.is_closed(): 
                              page.close()
                          logger.debug(f"User {self.user_id}: Page closed for task {self.user_id}.")
                      except Exception as close_page_error: 
                          logger.warning(f"User {self.user_id}: Error closing page during cleanup for task {self.user_id}: {close_page_error}")

                 # Chỉ đóng browser context nếu nó được tạo thành công
                 if browser_context: 
                     try: 
                          if browser_context.is_connected():
                              browser_context.close()
                          logger.debug(f"User {self.user_id}: Browser context closed for task {self.user_id}.")
                     except Exception as close_context_error: 
                         logger.warning(f"User {self_user_id}: Error closing browser context during cleanup for task {self.user_id}: {close_context_error}")

                 # 'with sync_playwright() as p:' tự động gọi p.stop() khi thoát block with
                 logger.info(f"User {self.user_id}: Playwright resource cleanup finished for task {self.user_id}.")

                 # === Sau khi xử lý xong MỘT tác vụ (dù thành công hay lỗi) ===
                 # === Báo hiệu item trong task queue đã xong ===
                 self._task_queue.task_done() 
                 logger.info(f"Worker thread {self.thread()}: Task {self.user_id} marked as done in queue.")


             except Exception as e:
                 # Bắt lỗi tổng quát trong block try lớn nhất (lỗi khởi tạo browser, v.v.) cho tác vụ hiện tại
                 logger.critical(f"User {self.user_id}: CRITICAL UNHANDLED ERROR during task execution for User {self.user_id}: {e}", exc_info=True)
                 self.signal_error.emit(self.user_id, f"User {self.user_id}: CRITICAL Task Error: {e}", self)
                 self.signal_status.emit(self.user_id, f"User {self.user_id}: CRITICAL Task Error.", self)
                 
                 # Cố gắng dọn dẹp thêm lần nữa như biện pháp dự phòng (có thể bỏ)
                 # if page: try: if not page.is_closed(): page.close() except Exception: pass 
                 # if browser_context: try: if browser_context.is_connected(): browser_context.close() except Exception: pass

                 # === Báo hiệu item trong task queue đã xong (dù bị lỗi nghiêm trọng) ===
                 # Cần đảm bảo task_done luôn được gọi cho mỗi item lấy ra từ queue
                 # Đặt task_done ở đây đảm bảo nó chạy khi lỗi xảy ra sau khi get task từ queue
                 # Hoặc đặt task_done ở finally của vòng lặp task chính
                 self._task_queue.task_done() 
                 logger.info(f"Worker thread {self.thread()}: Task {self.user_id} marked as done in queue (with critical error).")


             # --- Kết thúc khối try...except cho MỘT tác vụ ---
             # Vòng lặp chính `while True:` sẽ quay lại để lấy tác vụ tiếp theo nếu không bị break

         # --- Đây là code chạy SAU KHI VÒNG LẶP CHÍNH KẾT THÚC ---
         # Vòng lặp kết thúc khi break (hết tác vụ, bị dừng)
         logger.info(f"Worker thread {self.thread()}: Main task loop finished. Exiting thread.")
         
         # === Phát tín hiệu signal_finished CHỈ MỘT LẦN DUY NHẤT tại đây ===
         # Tín hiệu này báo hiệu rằng Worker đã hoàn thành xử lý TẤT CẢ các tác vụ được giao (hoặc đã bị dừng)
         # và thread sắp kết thúc.
         self.signal_finished.emit(self) # <-- Phát chính worker object (self)
         logger.info(f"Worker thread {self.thread()}: signal_finished emitted. Worker process ended.")
         # thread.quit() sẽ được gọi tự động sau tín hiệu này nhờ kết nối trong Service