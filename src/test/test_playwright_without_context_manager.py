# Cách làm thủ công (Không khuyến nghị cho các script thông thường)

from playwright.sync_api import sync_playwright
import time  # Chỉ dùng để tạm dừng cho ví dụ

# 1. Bắt đầu tiến trình Playwright một cách thủ công
p = None  # Khởi tạo biến
browser = None
context = None
page = None

try:
    # Bắt đầu Playwright (tương đương với __enter__ của context manager)
    p = sync_playwright().start()
    print("Đã bắt đầu Playwright thủ công.")

    # 2. Khởi chạy Browser, tạo Context, Page như bình thường
    browser = p.chromium.launch(headless=False)
    print("Đã khởi chạy Browser.")

    context = browser.new_context()
    print("Đã tạo Context.")

    page = context.new_page()
    print("Đã tạo Page.")

    # Thực hiện các thao tác trên page
    page.goto("https://example.com")
    print(f"Đã truy cập: {page.url}")
    time.sleep(5)  # Tạm dừng để bạn quan sát

    # 3. Đóng Page, Context, Browser một cách thủ công (quan trọng!)
    print("Đang đóng Page, Context, Browser thủ công...")
    if page:
        page.close()
        print("Page đã đóng.")
    if context:
        context.close()
        print("Context đã đóng.")
    if browser:
        browser.close()
        print("Browser đã đóng.")

    # 4. Dừng tiến trình Playwright backend một cách thủ công
    # Đây là bước quan trọng nhất để giải phóng tài nguyên hoàn toàn
    print("Đang dừng Playwright thủ công...")
    if p:
        p.stop()  # Tương đương với __exit__ của context manager
        print("Playwright đã dừng.")

except Exception as e:
    print(f"Đã xảy ra lỗi: {e}")
    # 5. Xử lý lỗi và đảm bảo đóng tài nguyên ngay cả khi có lỗi
    # Đây là phần phức tạp và dễ mắc lỗi khi làm thủ công
    print("Xảy ra lỗi, cố gắng đóng tài nguyên...")
    if page and not page.is_closed():  # Kiểm tra trước khi đóng
        try:
            page.close()
            print("Page đã đóng trong lỗi.")
        except:
            pass
    if context:  # Không có is_closed() cho context trực tiếp
        try:
            context.close()
            print("Context đã đóng trong lỗi.")
        except:
            pass
    if browser:
        if browser.is_connected():  # Kiểm tra kết nối trước khi đóng
            try:
                browser.close()
                print("Browser đã đóng trong lỗi.")
            except:
                pass
    if p:
        try:
            p.stop()
            print("Playwright đã dừng trong lỗi.")
        except:
            pass


print("Script kết thúc.")
