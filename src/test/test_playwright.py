import time
from playwright.sync_api import sync_playwright

# Thông tin proxy của bạn
# Định dạng server: 'protocol://host:port'
proxy_config = {
    "server": "171.236.161.110:35270",
    "username": "ByngId",
    "password": "rrgxOW",
}
# 171.236.161.110:35270:ByngId:rrgxOW

with sync_playwright() as p:
    # Khởi chạy trình duyệt với cấu hình proxy
    browser = p.chromium.launch(proxy=proxy_config, headless=False)

    # Tạo trang và kiểm tra IP
    page = browser.new_page()
    page.goto("http://httpbin.org/ip")  # Trang kiểm tra IP

    # Chờ cho nội dung IP hiển thị (cần điều chỉnh selector tùy trang)
    # Ví dụ với httpbin.org/ip, IP thường nằm trong thẻ <pre>
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

    # ... thực hiện các thao tác khác ...
    page.goto("https://www.whatismyip.com/")
    time.sleep(1000)
    # browser.close()
