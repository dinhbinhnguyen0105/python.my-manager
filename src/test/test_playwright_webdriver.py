from playwright.sync_api import sync_playwright

# Đoạn mã JavaScript để ghi đè thuộc tính webdriver
# Nó sẽ chạy trước khi bất kỳ script nào khác trên trang chạy
stealth_script = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined
});
"""

with sync_playwright() as p:
    # Khởi chạy trình duyệt (có thể thêm headless=True nếu cần)
    browser = p.chromium.launch(headless=False)

    # Tạo một context mới (hoặc dùng launch_persistent_context nếu cần profile)
    context = browser.new_context()

    # Thêm script này vào context.
    # Nó sẽ chạy trên MỌI trang được tạo trong context này.
    context.add_init_script(stealth_script)

    # Tạo trang từ context
    page = context.new_page()

    # Truy cập trang kiểm tra bot
    page.goto("https://bot.sannysoft.com/")

    print("Đang chờ kết quả kiểm tra trên bot.sannysoft.com...")

    # Đợi một chút để kết quả kiểm tra được hiển thị
    # (Bạn có thể cần điều chỉnh thời gian chờ hoặc sử dụng waits)
    page.wait_for_load_state("networkidle")  # Chờ mạng không hoạt động
    import time

    time.sleep(5)  # Đợi thêm vài giây để script trên trang chạy và cập nhật kết quả

    print("Kiểm tra kết quả trên trang. Tìm kiếm 'WebDriver'...")

    # Bạn có thể kiểm tra kết quả trực tiếp trên trang nếu muốn
    # Ví dụ: chụp ảnh màn hình để xem kết quả
    page.screenshot(path="sannysoft_check.png")
    print("Đã chụp ảnh màn hình kết quả: sannysoft_check.png")

    # (Tùy chọn) Thử lấy kết quả dưới dạng văn bản
    # Lưu ý: Cần tìm đúng selector chứa kết quả "WebDriver(New) present"
    # Selector có thể thay đổi trên trang sannysoft.com
    try:
        # Tìm element chứa kết quả WebDriver check
        # (Selector này có thể cần được cập nhật nếu trang thay đổi)
        webdriver_result_element = page.locator("text=WebDriver(New) present").first

        # Kiểm tra xem có chữ "present" và "failed" trong cùng dòng không
        if webdriver_result_element.count() > 0:
            parent_li = webdriver_result_element.locator("..")  # Lên thẻ cha li
            result_text = parent_li.inner_text()
            print(f"Kết quả kiểm tra WebDriver: {result_text}")
            if (
                "(failed)" not in result_text
                and "undefined" in result_text
                or "false" in result_text
            ):
                print("=> Có vẻ đã giấu được cờ WebDriver thành công!")
            else:
                print(
                    "=> Cờ WebDriver vẫn bị phát hiện hoặc kết quả không như mong đợi."
                )

    except Exception as e:
        print(f"Không thể lấy kết quả kiểm tra WebDriver từ trang: {e}")

    # Đóng context và browser
    context.close()
    browser.close()
    print("Đã đóng trình duyệt.")
