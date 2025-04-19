import pycurl
import io
import json
from urllib.parse import urlparse


def check_proxy(proxy_url):
    """
    Kiểm tra proxy có hoạt động được không bằng cách gọi http://httpbin.org/ip
    Trả về tuple: (is_ok: bool, message: str, detected_ip: str|None)
    """
    buffer = io.BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, "http://httpbin.org/ip")
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    curl.setopt(pycurl.CONNECTTIMEOUT, 5)  # timeout kết nối
    curl.setopt(pycurl.TIMEOUT, 5)  # timeout toàn bộ request

    # Thêm header giả lập trình duyệt thật để tránh 403
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept: application/json",
        "Accept-Language: en-US,en;q=0.9",
        "Connection: keep-alive",
    ]
    curl.setopt(pycurl.HTTPHEADER, headers)

    # Phân tích proxy_url dạng "http://user:pass@host:port"
    parsed = urlparse(proxy_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        curl.close()
        buffer.close()
        return False, "Invalid proxy URL", None

    curl.setopt(pycurl.PROXY, parsed.hostname)
    curl.setopt(pycurl.PROXYPORT, parsed.port or 80)
    if parsed.username and parsed.password:
        curl.setopt(pycurl.PROXYUSERPWD, f"{parsed.username}:{parsed.password}")

    try:
        curl.perform()
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        if code != 200:
            return False, f"HTTP Error: {code}", None

        body = buffer.getvalue().decode("utf-8")
        data = json.loads(body)
        ip = data.get("origin") or data.get("ip") or "Unknown IP"
        return True, "Proxy is working", ip

    except pycurl.error as e:
        errno, errstr = e.args
        return False, f"PyCurl error {errno}: {errstr}", None

    finally:
        curl.close()
        buffer.close()


def get_proxy(url):
    """
    Gọi API lấy proxy từ proxyxoay.shop, parse và kiểm tra với check_proxy()
    Trả về dict proxy hoặc False nếu thất bại.
    """
    buffer = io.BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.CONNECTTIMEOUT, 5)
    curl.setopt(pycurl.TIMEOUT, 5)

    # Thêm header để request API cũng giống trình duyệt
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept: application/json, text/plain, */*",
        "Accept-Language: en-US,en;q=0.9",
        "Referer: https://proxyxoay.shop/",
        "Connection: keep-alive",
    ]
    curl.setopt(pycurl.HTTPHEADER, headers)
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)

    try:
        curl.perform()
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        if code != 200:
            print(f"Failed to fetch proxy list, HTTP {code}")
            return False

        body = buffer.getvalue().decode("utf-8")
        res = json.loads(body)
        if res.get("status") != 100 or "proxyhttp" not in res:
            print("Invalid response from proxy API:", res)
            return False

        raw = res["proxyhttp"]  # ví dụ "42.117.243.215:10836:khljtiNj3Kd:fdkm3nbjg45d"
        ip, port, user, pwd = raw.split(":", 3)
        proxy_url = f"http://{user}:{pwd}@{ip}:{port}"

        ok, msg, detected_ip = check_proxy(proxy_url)
        if not ok:
            print("Proxy test failed:", msg)
            return False

        return {
            "username": user,
            "password": pwd,
            "server": f"{ip}:{port}",
        }

    except pycurl.error as e:
        errno, errstr = e.args
        print("PyCurl error when fetching proxies:", errstr)
        return False

    except Exception as e:
        print("Unexpected error:", str(e))
        return False

    finally:
        curl.close()
        buffer.close()


# Ví dụ sử dụng:
if __name__ == "__main__":
    proxy_api = (
        "https://proxyxoay.shop/api/get.php"
        "?key=TzINKouroeHgsrZcRudQfJ&nhamang=random&tinhthanh=0"
    )
    proxy_info = get_proxy(proxy_api)
    if proxy_info:
        print("Got proxy:", proxy_info)
    else:
        print("Cannot retrieve a working proxy.")
