# src/robot/browser_worker.py
import logging, random, sys, urllib
import queue, inspect, os, time  # Import time
from playwright.sync_api import (
    sync_playwright,
    Page,
    BrowserContext,
)  # Import BrowserContext
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)  # Import PlaywrightTimeoutError
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

# Import hàm get_proxy (đảm bảo nó hoạt động như get_proxy_pycurl đã thảo luận)
from src.utils.robot_handler import get_proxy

# Import các hàm hành động
# Ví dụ: từ một file actions.py
# from .actions import get_action_map
# Hoặc định nghĩa chúng ở đây tạm thời nếu chưa tách file


# === Ví dụ hàm hành động (định nghĩa ở đây hoặc import) ===
# Các hàm này nhận page, user_info (dict), và worker (QObject)
def do_launch_action(page: Page, user_info: dict, worker: QObject):
    """Logic cho hành động 'launch'."""
    logger = logging.getLogger(__name__)
    user_id = user_info.get("id", -1)
    logger.info(f"User {user_id}: Performing launch action.")
    worker.signal_status.emit(user_id, f"User {user_id}: Launching browser...", worker)
    try:
        page.goto("about:blank", timeout=30000)  # Ví dụ goto blank page, timeout 30s
        # Nếu muốn chờ browser mở cho người dùng xem, sử dụng wait_for_event("close")
        # worker.signal_status.emit(user_id, f"User {user_id}: Waiting for manual close...", worker)
        # page.wait_for_event("close", timeout=300000) # Chờ 5 phút
        logger.info(f"User {user_id}: Launch action completed.")
        worker.signal_status.emit(user_id, f"User {user_id}: Browser launched.", worker)
    except Exception as e:
        logger.error(f"User {user_id}: Launch action failed: {e}")
        # Ném lỗi để worker bắt và báo cáo
        raise


def do_discussion_action(page: Page, user_info: dict, worker: QObject):
    """Logic cho hành động 'discussion'."""
    logger = logging.getLogger(__name__)
    user_id = user_info.get("id", -1)
    action_info = user_info.get(
        "action_info", {}
    )  # Lấy thông tin cụ thể cho action này (post_info, groups)
    post_info = action_info.get("post_info")
    groups = action_info.get("groups", [])

    logger.info(f"User {user_id}: Performing discussion action.")
    worker.signal_status.emit(
        user_id, f"User {user_id}: Creating discussion...", worker
    )
    try:
        # === Logic Playwright cho hành động discussion ===
        # page.goto("http://example.com/create_discussion")
        # page.fill("#title", post_info.get("title"))
        # ... Playwright steps using post_info and groups ...
        time.sleep(random.uniform(10, 20))  # Giả lập thời gian làm việc

        logger.info(f"User {user_id}: Discussion action completed.")
        worker.signal_status.emit(user_id, f"User {user_id}: Discussion done.", worker)
    except Exception as e:
        logger.error(f"User {user_id}: Discussion action failed: {e}")
        raise


# === Dictionary ánh xạ tên hành động -> hàm ===
# Nên định nghĩa ở file actions.py và import
ACTION_MAP = {
    "launch": do_launch_action,
    "discussion": do_discussion_action,
    # Thêm các ánh xạ cho "marketplace", "interaction", "group"...
}


# Hàm log message (giữ lại từ code bạn)
def log_message(message):
    """In ra thông điệp kèm theo tên file và số dòng của nơi gọi hàm này."""
    caller_frame_record = inspect.stack()[1]
    frame = caller_frame_record[0]  # Lấy đối tượng frame
    info = inspect.getframeinfo(frame)

    filename = os.path.basename(info.filename)
    line_number = info.lineno

    # Sử dụng logger chuẩn thay cho print để nhất quán
    logging.getLogger(__name__).info(f"[{filename}:{line_number}] {message}")


# Cấu hình logger (đảm bảo level phù hợp, ví dụ INFO hoặc DEBUG)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(threadName)s - %(filename)s:%(lineno)d - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox",  # Rất quan trọng trên Linux/Docker
]


class BrowserWorker(QObject):
    signal_status = pyqtSignal(int, str, QObject)
    signal_error = pyqtSignal(int, str, QObject)
    signal_finished = pyqtSignal(QObject)
    signal_task_completed = pyqtSignal(int, QObject)

    def __init__(
        self,
        task_queue: queue.Queue,
        proxy_queue: queue.Queue,
        action_map: dict,  # <-- Nhận action map qua DI
        parent: QObject = None,
    ):
        super().__init__(parent)
        self._task_queue = task_queue
        self._proxy_queue = proxy_queue
        self._action_map = action_map  # Lưu action map

        # --- Các thuộc tính sẽ được cập nhật cho MỖI TÁC VỤ (item từ task_queue) ---
        self.user_id = -1
        self.user_type = ""
        self.user_ua = ""
        self.user_udd = ""
        self.headless = False
        # Thêm các thông tin khác cần truyền cho hàm hành động
        self.user_info = None  # Lưu toàn bộ user_info dict

        self.playwright_proxy_config = None  # Proxy cho tác vụ HIỆN TẠI

    @pyqtSlot()
    def run_task(self):
        # logger = logging.getLogger(__name__) # Nên lấy logger ở đây hoặc global
        logger.info(f"Worker thread {self.thread()} ({self}) started.")

        # --- Main loop để xử lý các đơn vị công việc từ task_queue ---
        while True:
            # === 1. Kiểm tra yêu cầu ngắt từ luồng chính ===
            if self.thread() and self.thread().isInterruptionRequested():
                logger.info(
                    f"Worker thread {self.thread()}: Interruption requested. Exiting task loop."
                )
                break  # Thoát khỏi vòng lặp chính

            work_item = None  # Khởi tạo biến để dùng trong finally

            # === 2. Lấy đơn vị công việc tiếp theo từ task_queue ===
            try:
                logger.debug(
                    f"Worker thread {self.thread()}: Waiting for next task item..."
                )
                # Lấy work_item. Block hoặc timeout (ví dụ 1s)
                work_item = self._task_queue.get(block=True, timeout=1)
                logger.info(
                    f"Worker thread {self.thread()}: Got task item. Tasks remaining: {self._task_queue.qsize()}."
                )

                # === Trích xuất thông tin từ đơn vị công việc (work_item) ===
                # work_item có cấu trúc {'user_info': {...}, 'action_index': ..., 'action_name': '...'}
                self.user_info = work_item.get(
                    "user_info", {}
                )  # Lưu toàn bộ user_info dict
                action_name = work_item.get("action_name", "unknown_action")
                self.action_index = work_item.get(
                    "action_index", -1
                )  # Lưu cho log/debug

                # === Cập nhật các thuộc tính worker từ user_info cho tác vụ HIỆN TẠI ===
                self.user_id = self.user_info.get(
                    "id", -1
                )  # Lấy user_id từ user_info dict
                self.user_type = self.user_info.get("type", "")
                self.user_ua = self.user_info.get("ua", "")
                self.user_udd = self.user_info.get("udd", "")  # Lấy UDD từ user_info
                self.headless = self.user_info.get(
                    "headless", False
                )  # Lấy headless từ user_info hoặc mặc định
                # Các thông tin khác (username, password, target_url...) cũng nên lấy từ user_info nếu cần cho action
                # self.username = self.user_info.get('login_details', {}).get('username')
                # self.password = self.user_info.get('login_details', {}).get('password')
                # self.target_url = self.user_info.get('target_url', 'about:blank')

                logger.info(
                    f"Worker thread {self.thread()}: Processing task for User ID {self.user_id}, Action '{action_name}'."
                )
                self.signal_status.emit(
                    self.user_id,
                    f"User {self.user_id}: Starting action '{action_name}'...",
                    self,
                )

            except queue.Empty:
                # === Hàng đợi tác vụ rỗng sau khi chờ timeout ===
                logger.info(
                    f"Worker thread {self.thread()}: Task queue is empty after timeout. Exiting task loop."
                )
                break  # Thoát khỏi vòng lặp chính khi hết tác vụ

            except Exception as e:
                # === Xử lý lỗi không mong muốn khi lấy task item từ queue (trừ queue.Empty) ===
                # Lỗi này hiếm, có thể break vòng lặp hoặc log và bỏ qua item lỗi (nếu item lỗi gây crash khi get)
                logger.critical(
                    f"Worker thread {self.thread()}: Error getting task item from queue: {e}",
                    exc_info=True,
                )
                # Báo lỗi (không có user_id cụ thể nếu lỗi ngay khi get)
                self.signal_error.emit(
                    self.user_id, f"Error getting task item from queue: {e}", self
                )
                # Quyết định: có bỏ qua item lỗi và tiếp tục không? (continue) Hay break?
                continue  # Thường continue để thử lấy item tiếp theo

            # === Logic xử lý MỘT ĐƠN VỊ CÔNG VIỆC (cho user_id, action_name đã lấy được) ===

            # Biến Playwright và proxy (khởi tạo cho mỗi lần xử lý task)
            playwright_proxy_config = None
            browser_context = None
            page = None

            try:  # Bắt lỗi cho toàn bộ quá trình xử lý 1 task item (lấy proxy, launch, action)

                # --- 3. Lấy proxy cho TÁC VỤ HIỆN TẠI ---
                # Logic lấy proxy từ _proxy_queue (y hệt code trước đó)
                # Cần đảm bảo self._proxy_queue tồn tại và không rỗng
                if self._proxy_queue and not self._proxy_queue.empty():
                    max_get_proxy_attempts = 5
                    raw_proxy_source_used = None

                    logger.info(
                        f"User {self.user_id}: Attempting to get proxy source for action '{action_name}'."
                    )
                    for attempt in range(1, max_get_proxy_attempts + 1):
                        # KIỂM TRA NGẮT TRONG VÒNG LẶP LẤY PROXY
                        if self.thread() and self.thread().isInterruptionRequested():
                            logger.info(
                                f"User {self.user_id}: Interruption requested during proxy fetch. Aborting task."
                            )
                            # Ném lỗi để thoát khối try/except/finally này và break vòng lặp chính
                            raise InterruptedError(
                                "Task interrupted during proxy fetch"
                            )

                        raw_source = None
                        try:
                            # === Get RAW PROXY SOURCE từ proxy_source_queue ===
                            # Dùng timeout để không block vô hạn và có thể kiểm tra ngắt
                            raw_source = self._proxy_queue.get(block=True, timeout=5.0)
                            logger.debug(
                                f"User {self.user_id}: Got raw proxy source: {raw_source}"
                            )

                            # === Gọi hàm get_proxy (thay thế get_proxy_pycurl) ===
                            # Hàm này cần nhận raw_source và trả về dict hoặc False
                            processed_proxy_dict = get_proxy(raw_source)

                            # === LUÔN gọi task_done() cho proxy_queue nếu đã lấy ra ===
                            self._proxy_queue.task_done()

                            if processed_proxy_dict:
                                playwright_proxy_config = processed_proxy_dict
                                raw_proxy_source_used = raw_source  # Lưu cho log
                                logger.info(
                                    f"User {self.user_id}: Successfully obtained proxy on attempt {attempt}."
                                )
                                break  # Thoát vòng lặp thử lấy proxy
                            else:
                                logger.warning(
                                    f"User {self.user_id}: Attempt {attempt}/{max_get_proxy_attempts} - get_proxy failed for {raw_source}. Trying next source."
                                )
                                # Nếu muốn thử lại nguồn này, put lại: self._proxy_queue.put(raw_source)

                        except queue.Empty:
                            logger.warning(
                                f"User {self.user_id}: Proxy source queue is empty after waiting. Cannot get proxy source for this task."
                            )
                            break  # Thoát vòng lặp thử lấy proxy
                        except Exception as e:
                            logger.error(
                                f"User {self.user_id}: Error calling get_proxy for {raw_source}: {e}",
                                exc_info=True,
                            )
                            # Lỗi nghiêm trọng khi gọi get_proxy (ví dụ: crash), nguồn proxy đã được task_done()
                            # Quyết định: có thử lại nguồn proxy này sau không?

                    # Log kết quả sau vòng lặp lấy proxy cho tác vụ này
                    if not playwright_proxy_config:
                        logger.warning(
                            f"User {self.user_id}: Failed to obtain a valid proxy after {max_get_proxy_attempts} attempts for task {action_name}. Proceeding without proxy."
                        )
                        self.signal_status.emit(
                            self.user_id,
                            f"User {self.user_id}: No proxy for '{action_name}'.",
                            self,
                        )

                else:
                    logger.info(
                        f"User {self.user_id}: Proxy source queue not available or empty. Proceeding without proxy for task {action_name}."
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: No proxy queue/empty.",
                        self,
                    )

                # === 4. Execute Playwright Automation cho TÁC VỤ HIỆN TẠI (chỉ 1 hành động) ===
                try:  # Bắt lỗi riêng cho Playwright và Action
                    logger.debug(
                        f"User {self.user_id}: Launching browser for action '{action_name}'."
                    )

                    with sync_playwright() as p:
                        # Build launch_options using self attributes đã cập nhật (user_udd, user_ua, headless)
                        launch_options = {
                            "user_data_dir": self.user_udd,
                            "headless": self.headless,
                            "args": PLAYWRIGHT_ARGS,  # Sử dụng args chung
                            "user_agent": self.user_ua,
                            "proxy": playwright_proxy_config,  # Sử dụng proxy đã lấy được
                        }
                        # Log thông tin proxy khi launch
                        if playwright_proxy_config:
                            logger.debug(
                                f"User {self.user_id}: Launching with proxy {playwright_proxy_config.get('server')} for '{action_name}'."
                            )
                        else:
                            logger.debug(
                                f"User {self.user_id}: Launching without proxy for '{action_name}'."
                            )

                        # Khởi chạy browser context
                        browser_context = p.chromium.launch_persistent_context(
                            **launch_options
                        )
                        page = browser_context.new_page()
                        logger.debug(f"User {self.user_id}: Browser launched.")

                        # === Tìm và gọi hàm thực thi hành động cụ thể ===
                        action_function = self._action_map.get(action_name)

                        if action_function:
                            logger.info(
                                f"User {self.user_id}: Executing action '{action_name}'."
                            )
                            # === Gọi hàm thực thi hành động ===
                            # Hàm này sẽ chứa logic Playwright cụ thể
                            # Truyền page, user_info và worker self
                            action_function(
                                page, self.user_info, self
                            )  # Truyền user_info dict, self

                            logger.info(
                                f"User {self.user_id}: Action '{action_name}' completed successfully."
                            )
                            # === Báo hiệu MỘT TÁC VỤ (cho user_id này) hoàn thành thành công ===
                            # Phát tín hiệu task_completed sau khi hành động Playwright hoàn thành
                            self.signal_task_completed.emit(self.user_id, self)
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Action '{action_name}' done.",
                                self,
                            )

                        # === Xử lý trường hợp action_name không hợp lệ ===
                        else:
                            logger.error(
                                f"User {self.user_id}: Unknown action name '{action_name}'. Skipping action."
                            )
                            self.signal_error.emit(
                                self.user_id,
                                f"User {self.user_id}: Unknown action '{action_name}'.",
                                self,
                            )
                            self.signal_status.emit(
                                self.user_id,
                                f"User {self.user_id}: Unknown action.",
                                self,
                            )

                        # --- Dọn dẹp tài nguyên Playwright cho tác vụ hiện tại ---
                        logger.debug(
                            f"User {self.user_id}: Attempting Playwright cleanup for '{action_name}'."
                        )
                        if page:
                            try:
                                if not page.is_closed():
                                    page.close()
                            except Exception as e:
                                logger.warning(
                                    f"User {self.user_id}: Error closing page: {e}"
                                )
                        if browser_context:
                            try:
                                if browser_context.is_connected():
                                    browser_context.close()
                            except Exception as e:
                                logger.warning(
                                    f"User {self.user_id}: Error closing browser context: {e}"
                                )
                        logger.debug(
                            f"User {self.user_id}: Playwright cleanup finished for '{action_name}'."
                        )

                    # 'with sync_playwright() as p:' tự động gọi p.stop()

                except InterruptedError:
                    # Đã xử lý ngắt ở các khối try con, chỉ cần log và thoát
                    logger.info(
                        f"User {self.user_id}: Task interrupted during action '{action_name}'. Exiting task processing try block."
                    )
                    pass  # Sẽ được bắt lại bởi except InterruptedError bên ngoài

                except PlaywrightTimeoutError as e:
                    logger.error(
                        f"User {self.user_id}: Playwright timeout during action '{action_name}': {e}",
                        exc_info=True,
                    )
                    self.signal_error.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{action_name}' timeout.",
                        self,
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{action_name}' timeout.",
                        self,
                    )

                except Exception as e:
                    logger.error(
                        f"User {self.user_id}: Error during action '{action_name}': {e}",
                        exc_info=True,
                    )
                    self.signal_error.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{action_name}' error: {e}.",
                        self,
                    )
                    self.signal_status.emit(
                        self.user_id,
                        f"User {self.user_id}: Action '{action_name}' error.",
                        self,
                    )

            # --- Khối finally cho việc xử lý MỘT ĐƠN VỊ CÔNG VIỆC ---
            # Khối này chạy SAU KHI khối try/except bên trên kết thúc (dù thành công hay lỗi)
            finally:
                # === Báo hiệu item từ task_queue đã xong ===
                # Điều này phải chạy SAU KHI worker đã xử lý xong đơn vị công việc này (kể cả cleanup Playwright)
                # work_item sẽ không phải là None nếu queue.get thành công
                if (
                    work_item is not None
                ):  # Chỉ gọi task_done nếu đã get được item từ queue
                    self._task_queue.task_done()
                    logger.debug(
                        f"Worker thread {self.thread()}: Work item for User {self.user_id}, Action '{action_name}' marked as done in queue."
                    )
                    logger.info(
                        f"Worker thread {self.thread()}: Task {self.user_id}, Action '{action_name}' finished processing. Tasks remaining: {self._task_queue.qsize()}"
                    )

                # === Kiểm tra ngắt lần nữa sau khi xử lý xong 1 task item ===
                if self.thread() and self.thread().isInterruptionRequested():
                    logger.info(
                        f"Worker thread {self.thread()}: Interruption requested after processing task {self.user_id}, action '{action_name}'. Exiting task loop."
                    )
                    break  # Thoát khỏi vòng lặp chính

        # --- Code chạy SAU KHI VÒNG LẶP CHÍNH while True kết thúc ---
        # Vòng lặp kết thúc khi break (hết tác vụ trong queue hoặc bị yêu cầu dừng)
        logger.info(
            f"Worker thread {self.thread()} ({self}): Main task loop finished. Exiting thread."
        )

        # === Phát tín hiệu signal_finished CHỈ MỘT LẦN DUY NHẤT tại đây ===
        self.signal_finished.emit(self)
        logger.info(
            f"Worker thread {self.thread()} ({self}): signal_finished emitted. Worker process ended."
        )
        # thread.quit() sẽ được gọi tự động sau tín hiệu này nhờ kết nối trong Service


# --- Implement the get_proxy function ---
# This function should take a raw_proxy_source_string and return a Playwright proxy dict or False
# It should include PycURL logic for fetching/checking as discussed
def get_proxy(raw_proxy_source: str) -> dict | bool:
    """Placeholder for the actual proxy fetching and checking logic."""
    logger = logging.getLogger(__name__)
    logger.info(f"Executing get_proxy for source: {raw_proxy_source}")

    # === Replace with your actual PycURL code ===
    # This part involves network I/O and should be robust
    try:
        # Example: Simulate fetching and checking
        time.sleep(random.uniform(0.5, 2.0))

        # Simulate success/failure
        if (
            "fail" in raw_proxy_source.lower() or random.random() < 0.1
        ):  # 10% chance of failure
            logger.warning(f"Simulating proxy check failure for {raw_proxy_source}")
            return False

        # Simulate parsing into Playwright format
        # Assuming format is type://user:pass@host:port or API URL
        parsed = urllib.parse.urlparse(raw_proxy_source)
        proxy_config = {}
        if parsed.scheme in ["http", "https", "socks5"]:
            proxy_config["server"] = (
                f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            )
            if parsed.username:
                proxy_config["username"] = parsed.username
            if parsed.password:
                proxy_config["password"] = parsed.password
        # Add logic for API sources if get_proxy handles that too
        elif parsed.hostname == "proxyxoay.shop":
            # Simulate API call and response parsing
            logger.debug(f"Simulating API call for {raw_proxy_source}")
            time.sleep(random.uniform(1, 3))
            mock_api_response = {
                "status": 100,
                "proxyhttp": "1.2.3.4:5678:testuser:testpass",
            }  # Example
            if (
                mock_api_response.get("status") == 100
                and "proxyhttp" in mock_api_response
            ):
                raw_proxy_data = mock_api_response["proxyhttp"]
                parts = raw_proxy_data.split(":")
                if len(parts) == 4:
                    ip, port, user, pwd = parts
                    proxy_config = {
                        "server": f"{ip}:{port}",
                        "username": user,
                        "password": pwd,
                    }
                    # You might add a final check of this obtained proxy here
                    logger.info(f"Successfully simulated API proxy get: {ip}:{port}")
                    return proxy_config
            logger.warning(f"Simulating API call failure for {raw_proxy_source}")
            return False  # API call or parse failed
        else:
            logger.warning(
                f"Unsupported scheme or format in simulation: {raw_proxy_source}"
            )
            return False

        logger.info(f"Successfully simulated proxy check for {raw_proxy_source}")
        return proxy_config

    except Exception as e:
        logger.error(
            f"Error in get_proxy simulation for {raw_proxy_source}: {e}", exc_info=True
        )
        return False
