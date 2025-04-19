from playwright.sync_api import sync_playwright

stealth_script = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined
});
"""
proxy_config = {
    "server": "171.236.161.110:35270",
    "username": "ByngId",
    "password": "rrgxOW",
}

with sync_playwright() as p:
    browser_context = p.chromium.launch_persistent_context(
        user_data_dir="/Volumes/KINGSTON/Dev/python/pyhon.my-manager/repositories/users/udd/1",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
        proxy=proxy_config,
        headless=False,
    )
    browser_context.add_init_script(stealth_script)
    page = browser_context.new_page()
    page.goto("http://httpbin.org/ip")

    try:
        ip_element = page.locator("body pre").first
        detected_ip_text = ip_element.inner_text()
        import json

        ip_data = json.loads(detected_ip_text)
        detected_ip = ip_data.get("origin")
        print(f"Địa chỉ IP công cộng được phát hiện qua proxy: {detected_ip}")
    except Exception as e:
        print(f"Không thể lấy IP hoặc phân tích nội dung: {e}")
        print("Nội dung trang nguồn:", page.content())

    page.goto("https://bot.sannysoft.com/", timeout=60000)
    page.goto("https://www.facebook.com/", timeout=60000)
    import time

    time.sleep(100000)
