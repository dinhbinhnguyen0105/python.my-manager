import urllib.request
import json  # Cần module json để xử lý JSON

api_url = "https://jsonplaceholder.typicode.com/posts/1"

try:
    # Mở URL
    with urllib.request.urlopen(api_url) as response:
        # Đọc nội dung phản hồi
        data = response.read().decode("utf-8")

        # Chuyển đổi chuỗi JSON thành dictionary Python
        json_data = json.loads(data)

        print("GET Request (urllib) thành công:")
        print(json_data)

except urllib.error.URLError as e:
    print(f"Lỗi trong quá trình GET Request (urllib): {e.reason}")
except Exception as e:
    print(f"Lỗi khác: {e}")
