# src/robot/browser_worker.py

import time
from playwright.sync_api import sync_playwright, Page, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from PyQt6.QtCore import QObject

from src.utils.logger import log
from src.robot import selectors
from src.robot.browser_actions import ACTION_MAP
from src.utils.robot_handler import get_proxy


PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox",
]
network_conditions = {
    "offline": {
        "offline": True,
        "latency": 0,
        "download_throughput": -1,  # Không áp dụng khi offline
        "upload_throughput": -1,  # Không áp dụng khi offline
    },
    "Slow 3G": {
        "offline": False,
        # Tốc độ download (ví dụ: 500 kbps -> 500 * 1024 / 8 bytes/s)
        "download_throughput": int(500 * 1024 / 8),
        # Tốc độ upload (ví dụ: 256 kbps -> 256 * 1024 / 8 bytes/s)
        "upload_throughput": int(256 * 1024 / 8),
        "latency": 400,  # Độ trễ 400ms
    },
    "Fast 3G": {
        "offline": False,
        "download_throughput": int(1.5 * 1024 * 1024 / 8),  # 1.5 Mbps
        "upload_throughput": int(750 * 1024 / 8),  # 750 kbps
        "latency": 150,  # 150ms
    },
    # Thêm các cấu hình khác nếu cần...
    "No Throttling": {  # Để tắt throttling
        "offline": False,
        "latency": 0,
        "download_throughput": -1,
        "upload_throughput": -1,
    },
}


def set_network_throttling(page: Page, condition_name: str):
    """Đặt giới hạn mạng cho page sử dụng CDP."""
    if condition_name not in network_conditions:
        print(f"Cảnh báo: Không tìm thấy cấu hình mạng '{condition_name}'. Bỏ qua.")
        return

    conditions = network_conditions[condition_name]
    print(f"Đang áp dụng giới hạn mạng: {condition_name}...")
    try:
        # Tạo session CDP gắn với page này
        cdp_session = page.context.new_cdp_session(page)
        # Gửi lệnh giả lập mạng
        cdp_session.send(
            "Network.emulateNetworkConditions",
            {
                "offline": conditions["offline"],
                "latency": conditions["latency"],
                "downloadThroughput": conditions["download_throughput"],
                "uploadThroughput": conditions["upload_throughput"],
                # 'connectionType': 'cellular3g' # Có thể thêm nếu muốn
            },
        )
        print("-> Áp dụng thành công.")
    except Exception as e:
        # CDP có thể không được hỗ trợ đầy đủ trên Firefox/WebKit
        print(f"-> Lỗi khi đặt giới hạn mạng qua CDP: {e}")
        print(
            "   Lưu ý: Giả lập mạng qua CDP hoạt động tốt nhất với trình duyệt Chromium."
        )


def discussion(payload):
    if not payload.get("proxy"):
        return
    browser_option = {
        "proxy": payload.get("proxy", None),
        "screen": {"width": 1920, "height": 1080},
        # "screen": {"width": 1080, "height": 760},
        "user_data_dir": payload.get("user_data_dir"),
        "headless": payload.get("headless"),
        "args": PLAYWRIGHT_ARGS,
        "user_agent": payload.get("user_agent", None),
    }

    with sync_playwright() as p:
        try:
            browser_context = p.chromium.launch_persistent_context(**browser_option)
            log(f"Browser launched.")
            page = browser_context.new_page()

            # set_network_throttling(page, "Slow 3G")

            # page.wait_for_event("close", timeout=0)

            action_function = ACTION_MAP["discussion"]
            action_function(
                page,
                25,
                {
                    "title": "[8.0 TRIỆU/THÁNG]CHO THUÊ NHÀ PHỐ CÓ NỘI THẤT CƠ BẢN TẠI ĐÀ LẠT",
                    "description": """
Cho thuê nhà phố ID: re.r.9b486dd3 ️🏆❄
Đ/c: Phường 5, Đà Lạt
🛌 Công năng: 1pk, 1 bếp, 2pn
+ Nhà đẹp, sân để xe hơi rộng rãi
+ Gác rộng 30m2
------------
💵 Giá: 8.0triệu/tháng 👗🎒
Lh: 0375.155.525
------------------
Ký gửi mua, bán - cho thuê, thuê bất động sản xin liên hệ 0375.155.525 - Mr. Bình
------------------

[
    pid <re.r.9b486dd3>
    updated_at <2025-04-24 01:46:32>
    published_at <2025-04-24 09:28:30>
]
                    """,
                    "images": [
                        "/Volumes/KINGSTON/Dev/python/python.my-manager/repositories/products/re/45/45_0.jpg",
                        "/Volumes/KINGSTON/Dev/python/python.my-manager/repositories/products/re/45/45_1.jpg",
                    ],
                },
                QObject(),
            )

        except Exception as e:
            log(f"ERROR {e}")
            raise Exception(e)


if __name__ == "__main__":
    proxy = get_proxy(
        "https://proxyxoay.shop/api/get.php?key=XpqQkCrWTuxCQfGrVJNkYq&&nhamang=random&&tinhthanh=0"
    )
    print(proxy)
    discussion(
        {
            "proxy": proxy,
            # "user_data_dir": "/Volumes/KINGSTON/Dev/python/python.my-manager/repositories/users/udd/test",
            "user_data_dir": "/Volumes/KINGSTON/Dev/python/python.my-manager/repositories/users/udd/10",
            # "user_data_dir": "/Users/ndb/Dev/python/python.my-manager/repositories/users/udd/2",
            "headless": False,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        }
    )
