# src/robot/browser_worker.py

import time
from playwright.sync_api import sync_playwright, Page, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.utils.logger import log
from src.robot import selectors


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
    browser_option = {
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
            page = browser_context.new_page()
            log(f"Browser launched.")
            page.wait_for_event("close", timeout=0)

            return
            # set_network_throttling(page, "Slow 3G")
            page.goto("https://www.facebook.com/groups/feed/")

            page_language = page.locator("html").get_attribute("lang")
            sidebar_elm = page.locator(
                f"{selectors.S_NAVIGATION}:not({selectors.S_BANNER} {selectors.S_NAVIGATION})"
            )
            while sidebar_elm.locator(selectors.S_LOADING).count():
                _ = sidebar_elm.locator(selectors.S_LOADING)
                if _.count():
                    try:
                        time.sleep(0.3)
                        _.first.scroll_into_view_if_needed(timeout=100)
                    except:
                        pass
            group_urls = []

            group_elms = sidebar_elm.locator(
                "a[href^='https://www.facebook.com/groups/']"
            ).all()

            for group_elm in group_elms:
                group_url = group_elm.get_attribute("href")
                group_urls.append(
                    group_url if not group_url.endswith("/") else group_url[:-1]
                )
                # time.sleep(0.3)
                group_elm.scroll_into_view_if_needed(timeout=10000)
                group_elm.highlight()
                group_elm.click(timeout=10000)
                time.sleep(1)
                main_locator = page.locator(selectors.S_MAIN)
                tablist_locator = main_locator.first.locator(selectors.S_TABLIST)
                try:
                    tablist_locator.first.wait_for(state="attached", timeout=2000)
                    if not tablist_locator.count():
                        log("continue")
                        continue
                    log(f"count: {tablist_locator.count()}")
                except Exception as e:
                    log(f"continue: {e}")
                    continue

                tab_locator = tablist_locator.first.locator(selectors.S_TABLIST_TAB)
                is_discussion = False
                tab_url = ""
                for tab_elm in tab_locator.all():
                    is_discussion = True
                    tab_url = tab_elm.get_attribute("href")
                    if not tab_url:
                        continue
                    tab_url = tab_url[:-1] if tab_url.endswith("/") else tab_url
                    if tab_url.endswith == "buy_sell_discussion":
                        is_discussion = False
                        break
                if is_discussion:
                    profile_locator = main_locator.first.locator(
                        selectors.S_PROFILE(page_language)
                    )
                    if not profile_locator.count():
                        log("continue")
                        continue
                    time.sleep(1)
                    profile_locator.first.wait_for(state="attached", timeout=10000)
                    profile_locator.first.scroll_into_view_if_needed(timeout=10000)
                    button_elm = profile_locator.first
                    while True:
                        if button_elm.locator("..").locator(selectors.S_BUTTON).count():
                            button_elm = button_elm.locator("..").locator(
                                selectors.S_BUTTON
                            )
                            break
                        else:
                            button_elm = button_elm.locator("..")
                    time.sleep(1)
                    button_elm.first.scroll_into_view_if_needed(timeout=10000)
                    button_elm.first.highlight()
                    time.sleep(1)
                    try:
                        button_elm.first.click(timeout=10000)
                    except:
                        continue

                    # log(button_elm.first.inner_html())

                    dialog_create_post_elm = page.locator(
                        selectors.S_DIALOG_CREATE_POST(page_language)
                    ).first
                    dialog_create_post_elm.highlight()
                    dialog_loading_elm = dialog_create_post_elm.locator(
                        selectors.S_LOADING
                    ).first
                    dialog_loading_elm.wait_for(state="detached")

                    dialog_create_post_elm = dialog_create_post_elm.locator(
                        "xpath=ancestor::*[contains(@role, 'dialog')][1]"
                    ).first
                    dialog_create_post_elm.highlight()

                    text_box_elm = dialog_create_post_elm.locator(
                        selectors.S_TEXTBOX
                    ).first
                    text_box_elm.fill("bla", timeout=1000)

                    close_btn_elm = dialog_create_post_elm.locator(
                        selectors.S_CLOSE_BUTTON(page_language)
                    ).first
                    close_btn_elm.highlight()
                    time.sleep(0.3)
                    try:
                        close_btn_elm.wait_for(state="attached", timeout=(10000))
                    except:
                        # log(dialog_create_post_elm.inner_html())
                        page.wait_for_event("close", timeout=0)
                    close_btn_elm.click(timeout=10000)
                    dialog_create_post_elm.wait_for(state="detached", timeout=30000)
                    # page.wait_for_event("close", timeout=0)

            page.wait_for_event("close", timeout=0)
        except Exception as e:
            log(f"ERROR {e}")
            raise Exception(e)


if __name__ == "__main__":
    discussion(
        {
            # "user_data_dir": "/Volumes/KINGSTON/Dev/python/python.my-manager/repositories/users/udd/7",
            "user_data_dir": "/Users/ndb/Dev/python/python.my-manager/repositories/users/udd/2",
            "headless": False,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        }
    )
