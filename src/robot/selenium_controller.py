# src/robot/selenium_controller.py
import undetected_chromedriver as uc
from urllib.parse import urlparse  # Import để phân tích chuỗi URL proxy


class SeleniumController:
    def __init__(self, payload):
        self.udd = payload.get("udd", None)
        self.proxy = payload.get("proxy", None)
        self.ua = payload.get("ua", None)

    def init_driver(self):
        if not self.proxy or not self.udd or not self.ua:
            return False
        try:
            print(self.proxy)  # http://khljtiNj3Kd:fdkm3nbjg45d@14.245.117.96:21290
            proxy_url = f"{self.proxy.get('ip')}:{self.proxy.get('port')}"
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument(f"--user-data-dir={self.udd}")
            chrome_options.add_argument(f"--user-agent={self.ua}")
            chrome_options.add_argument("--profile-directory=Default")
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = uc.Chrome(options=chrome_options)

            return driver
        except Exception as e:
            print(e)
