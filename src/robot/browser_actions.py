import random
from time import sleep
from PyQt6.QtCore import QObject
from playwright.sync_api import Page
from src.utils.logger import log
from src.robot import selectors


def do_launch_action(page: Page, user_id, action_info: dict, worker: QObject):
    log(f"User {user_id}: Performing launch action.")
    try:
        page.wait_for_event("close", timeout=0)
        log(f"User {user_id}: Launch action completed.")
        worker.signal_status.emit(user_id, f"User {user_id}: Browser launched.", worker)
    except Exception as e:
        log(f"User {user_id}: Launch action failed: {e}")


def do_discussion_action(page: Page, user_id, action_info: dict, worker: QObject):
    log(f"User {user_id}: Performing launch action.")
    groups = action_info.get("groups", [])
    title = action_info.get("title")
    description = action_info.get("description")
    images = action_info.get("images", [])
    max_groups = 5
    current_group = 0
    if len(groups):
        pass
    else:
        # try:
        page.goto("http://httpbin.org/ip")
        origin_locator = page.locator("pre")
        print(f"user_id: {user_id} - {origin_locator.first.text_content()}")
        sleep(30)
        return
        page.goto("https://www.facebook.com/groups/feed/", timeout=60000)
        page_language = page.locator("html").get_attribute("lang")
        if page_language != "en":
            log("This robot does not support Vietnamese, please switch to English.")
            return
        sidebar_locator = page.locator(
            f"{selectors.S_NAVIGATION}:not({selectors.S_BANNER} {selectors.S_NAVIGATION})"
        )
        while sidebar_locator.first.locator(selectors.S_LOADING).count():
            _ = sidebar_locator.first.locator(selectors.S_LOADING)
            if _.count():
                try:
                    random_sleep(1, 3)
                    _.first.scroll_into_view_if_needed(timeout=100)
                except:
                    break
        group_locators = sidebar_locator.first.locator(
            "a[href^='https://www.facebook.com/groups/']"
        )
        group_urls = []
        for group_locator in group_locators.all():
            group_urls.append(group_locator.get_attribute("href"))
        for group_url in group_urls:
            page.goto(group_url, timeout=60_000)
            main_locator = page.locator(selectors.S_MAIN)
            tablist_locator = main_locator.first.locator(selectors.S_TABLIST)
            try:
                tablist_locator.first.wait_for(state="attached", timeout=5_000)
            except:
                continue
            tab_locators = tablist_locator.first.locator(selectors.S_TABLIST_TAB)
            is_discussion = False
            for tab_locator in tab_locators.all():
                is_discussion = True
                tab_url = tab_locator.get_attribute("href", timeout=5_000)
                if not tab_url:
                    continue
                tab_url = tab_url[:-1] if tab_url.endswith("/") else tab_url
                if tab_url.endswith == "buy_sell_discussion":
                    is_discussion = False
                    break
            if is_discussion:
                profile_locator = main_locator.first.locator(selectors.S_PROFILE)
                try:
                    profile_locator.first.wait_for(state="attached", timeout=60_000)
                except:
                    log("continue!")
                    continue
                random_sleep(1, 3)
                profile_locator.first.scroll_into_view_if_needed()
                discussion_btn_locator = profile_locator
                while True:
                    if (
                        discussion_btn_locator.first.locator("..")
                        .locator(selectors.S_BUTTON)
                        .count()
                    ):
                        discussion_btn_locator = discussion_btn_locator.first.locator(
                            ".."
                        ).locator(selectors.S_BUTTON)
                        break
                    else:
                        discussion_btn_locator = discussion_btn_locator.first.locator(
                            ".."
                        )
                random_sleep(1, 3)
                discussion_btn_locator.first.scroll_into_view_if_needed()
                discussion_btn_locator.first.highlight()
                try:
                    discussion_btn_locator.first.click()
                except:
                    continue

                page.locator(selectors.S_DIALOG_CREATE_POST).first.locator(
                    selectors.S_LOADING
                ).first.wait_for(state="detached", timeout=30_000)
                dialog_locator = page.locator(selectors.S_DIALOG_CREATE_POST)
                dialog_locator.first.highlight()
                dialog_container_locator = dialog_locator.first.locator(
                    "xpath=ancestor::*[contains(@role, 'dialog')][1]"
                )

                dialog_container_locator.first.highlight()

                if len(images):
                    image_btn_locator = dialog_container_locator.first.locator(
                        selectors.S_IMAGE_BUTTON
                    )
                    image_btn_locator.first.highlight()
                    random_sleep(1, 3)
                    image_btn_locator.click()

                    image_input_locator = dialog_container_locator.locator(
                        selectors.S_IMG_INPUT
                    )
                    random_sleep(1, 3)
                    image_input_locator.set_input_files(images, timeout=10000)

                textbox_locator = dialog_container_locator.first.locator(
                    selectors.S_TEXTBOX
                )
                random_sleep(1, 3)
                textbox_locator.fill(title + "\n" + description)
                post_btn_locators = dialog_container_locator.first.locator(
                    selectors.S_POST_BUTTON
                )

                # ?not true?
                dialog_container_locator.locator(
                    f"{selectors.S_POST_BUTTON}[aria-disabled]"
                ).wait_for(state="detached", timeout=30_000)

                # :not([aria-disabled])
                post_btn_locators.first.click()
                dialog_container_locator.wait_for(state="detached", timeout=60_000)
                random_sleep(1, 3)
            else:
                continue

            if current_group >= max_groups:
                break
            current_group += 1


def random_sleep(min_delay: float = 0.1, max_delay: float = 0.5):
    delay = random.uniform(min_delay, max_delay) * 1
    sleep(delay)


ACTION_MAP = {
    "launch": do_launch_action,
    "discussion": do_discussion_action,
}
