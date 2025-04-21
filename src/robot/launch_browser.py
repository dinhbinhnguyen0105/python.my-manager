import logging, sys
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def launch_browser(proxy, udd, ua):
    stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
        });
    """

    try:
        p = sync_playwright().start()
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=udd,
            proxy=proxy,
            user_agent=ua,
            headless=False,
        )
        browser_context.add_init_script(stealth_script)
        page = browser_context.new_page()
        page.wait_for_event("close", timeout=0)
        if page:
            page.close()
        if browser_context:
            browser_context.close()
        if p:
            p.stop()

        # closed

    except Exception as e:
        if page and not page.is_closed():
            try:
                page.close()
                print("Page closed on error.")
            except:
                pass
        if browser_context:
            if browser_context.is_connected():
                try:
                    browser_context.close()
                    print("Browser closed on error.")
                except:
                    pass
        if p:
            try:
                p.stop()
                print("Playwright stopped on error.")
            except:
                pass


if __name__ == "__main__":
    proxy_config = {
        "server": "171.236.161.110:35270",
        "username": "ByngId",
        "password": "rrgxOW",
    }
    user_data_dir = (
        "/Volumes/KINGSTON/Dev/python/pyhon.my-manager/repositories/users/udd/1"
    )
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    launch_browser(proxy=proxy_config, udd=user_data_dir, ua=user_agent)
