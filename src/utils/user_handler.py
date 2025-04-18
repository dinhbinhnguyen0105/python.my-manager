import requests
from urllib.parse import quote_plus
from urllib.parse import urlparse


def check_proxy(proxy_url):
    proxies = {"http": proxy_url, "https": proxy_url}

    test_url = "http://httpbin.org/ip"

    try:
        response = requests.get(test_url, proxies=proxies, timeout=1)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        ip_data = response.json()
        print(ip_data)
        detected_ip = ip_data.get("origin", "Unknown IP")
        return True, "Proxy is working", detected_ip

    except requests.exceptions.Timeout:
        return (
            False,
            f"Proxy did not respond within 1 seconds (Timeout).",
            None,
        )
    except requests.exceptions.ConnectionError as e:
        return (
            False,
            f"Could not connect to the proxy or target website: {e}",
            None,
        )
    except requests.exceptions.RequestException as e:
        return False, f"Request error via proxy: {e}", None
    except Exception as e:
        return False, f"Unknown error: {e}", None


def get_proxies(url):
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname == "proxyxoay.shop":
            res = requests.get(url, timeout=1)
            res = res.json()
            if res.get("status") == 100:
                proxy_raw = res.get("proxyhttp")
                proxy_split = proxy_raw.split(":")
                proxy = f"http://{proxy_split[2]}:{proxy_split[3]}@{proxy_split[0]}:{proxy_split[1]}"
                # "42.117.243.215:10836:khljtiNj3Kd:fdkm3nbjg45d"
                if check_proxy(proxy):
                    return {
                        "username": proxy_split[2],
                        "password": proxy_split[3],
                        "ip": proxy_split[0],
                        "port": proxy_split[1],
                    }
        return False
    except Exception as e:
        print(str(e))
        return False
