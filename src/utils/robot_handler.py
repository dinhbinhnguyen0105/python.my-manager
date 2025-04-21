import queue, io, pycurl, json
from urllib.parse import urlparse
from typing import Any, Dict, Optional, Tuple


def get_proxy(proxy_raw: str) -> Dict:
    buffer = io.BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, proxy_raw)
    curl.setopt(pycurl.CONNECTTIMEOUT, 5)
    curl.setopt(pycurl.TIMEOUT, 5)
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
        if code != 200:
            return None

        body = buffer.getvalue().decode("utf-8")
        res = json.loads(body)
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
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    curl.setopt(pycurl.CONNECTTIMEOUT, 5)
    curl.setopt(pycurl.TIMEOUT, 5)
    headers = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept: application/json",
        "Accept-Language: en-US,en;q=0.9",
        "Connection: keep-alive",
    ]
    curl.setopt(pycurl.HTTPHEADER, headers)

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
        print(ip)
        return True

    except pycurl.error as e:
        errno, errstr = e.args
        return False

    finally:
        curl.close()
        buffer.close()


def fetch_task_data(task_queue: queue.Queue) -> Optional[Dict[str, Any]]:
    try:
        raw = task_queue.get(block=True, timeout=1000)
        task_queue.task_done()
    except queue.Empty:
        return None
    except Exception as e:
        print("ERROR [fetch_task_data]: ", e)
    return raw


def fetch_proxy_data(
    proxy_queue: queue.Queue, max_attempts: int = 5
) -> Optional[Dict[str, Any]]:
    for attempt in range(max_attempts):
        try:
            raw = proxy_queue.get(block=True)
            proxy_queue.task_done()
        except queue.Empty:
            break
        try:
            proxy = get_proxy(raw)
        except Exception:
            continue
        if proxy:
            return proxy

    return None
