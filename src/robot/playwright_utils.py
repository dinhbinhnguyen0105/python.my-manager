from playwright.sync_api import Page, BrowserContext, Browser, Playwright


def handle_exception(
    page: Page, context: BrowserContext, browser: Browser, playwright: Playwright
):
    if page and not page.is_closed():
        try:
            page.close()
            print("Page closed on error.")
        except:
            pass
    if context:
        try:
            context.close()
            print("Context closed on error.")
        except:
            pass
    if browser:
        if browser.is_connected():
            try:
                browser.close()
                print("Browser closed on error.")
            except:
                pass
    if playwright:
        try:
            playwright.stop()
            print("Playwright stopped on error.")
        except:
            pass
