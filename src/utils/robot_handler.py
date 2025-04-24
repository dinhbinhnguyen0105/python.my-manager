import queue, io, pycurl, json
from urllib.parse import urlparse, parse_qs
from typing import Dict


def get_proxy(proxy_raw: str) -> Dict:
    buffer = io.BytesIO()
    curl = pycurl.Curl()
    # https://proxyxoay.shop/api/get.php?key=[keyxoay]&&nhamang=random&&tinhthanh=0
    curl.setopt(pycurl.URL, proxy_raw)
    curl.setopt(pycurl.CONNECTTIMEOUT, 30)
    curl.setopt(pycurl.TIMEOUT, 30)
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept: application/json, text/plain, */*",
        "Accept-Language: en-US,en;q=0.9",
        "Referer: https://proxyxoay.shop/",
        "Connection: keep-alive",
    ]
    curl.setopt(pycurl.HTTPHEADER, headers)
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    curl.perform()
    try:
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        body = buffer.getvalue().decode("utf-8")
        res = json.loads(body)
        parsed_url = urlparse(proxy_raw)
        query_params = parse_qs(parsed_url.query)
        key = query_params.get("key", [None])[0]
        print(f"{key} - {res.get('proxyhttp', 'Invalid')}")
        if code != 200:
            return None
        if res.get("status") != 100 or "proxyhttp" not in res:
            return None

        raw = res["proxyhttp"]
        ip, port, user, pwd = raw.split(":", 3)
        proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
        if not check_proxy(proxy_url):
            return None

        return {
            "username": user,
            "password": pwd,
            "server": f"{ip}:{port}",
        }

    except pycurl.error as e:
        errno, errstr = e.args
        return None

    except Exception as e:
        return None

    finally:
        curl.close()
        buffer.close()


def check_proxy(proxy: str) -> bool:
    buffer = io.BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, "http://httpbin.org/ip")
    curl.setopt(pycurl.CONNECTTIMEOUT, 30)
    curl.setopt(pycurl.TIMEOUT, 30)
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept: application/json, text/plain, */*",
        "Accept-Language: en-US,en;q=0.9",
        "Connection: keep-alive",
    ]
    curl.setopt(pycurl.HTTPHEADER, headers)
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)

    parsed = urlparse(proxy)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        curl.close()
        buffer.close()
        return False

    curl.setopt(pycurl.PROXY, parsed.hostname)
    curl.setopt(pycurl.PROXYPORT, parsed.port or 80)
    if parsed.username and parsed.password:
        curl.setopt(pycurl.PROXYUSERPWD, f"{parsed.username}:{parsed.password}")
    try:
        curl.perform()
        code = curl.getinfo(pycurl.RESPONSE_CODE)
        if code != 200:
            return False

        body = buffer.getvalue().decode("utf-8")
        data = json.loads(body)
        ip = data.get("origin") or data.get("ip") or "Unknown IP"
        return True

    except pycurl.error as e:
        errno, errstr = e.args
        return False

    finally:
        curl.close()
        buffer.close()
