import random, traceback, sys
from time import sleep
from PyQt6.QtCore import QObject, pyqtSignal
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from typing import Tuple
from src.robot import selectors
from src.my_types import BrowserInfo, ActionInfo, TaskInfo


class WorkerSignals(QObject):
    log_message = pyqtSignal(str)
    error = pyqtSignal((TaskInfo, int, str))
    finished = pyqtSignal((TaskInfo, int))
    progress = pyqtSignal(int)


def random_sleep(min_delay: float = 0.1, max_delay: float = 0.5):
    delay = random.uniform(min_delay, max_delay) * 1
    sleep(delay)


def do_launch(
    page: Page,
    browser_info: BrowserInfo,
    action_info: ActionInfo,
    signals: WorkerSignals,
):
    try:
        # page.goto("https://www.facebook.com", timeout=60000)
        signals.log_message.emit("f[{browser_info.user_id}] Wait for closing ...")
        page.wait_for_event("close", timeout=900_000)
        signals.log_message.emit(f"[{browser_info.user_id}] Closed!")
    except Exception as e:
        exc_type, value, tb = sys.exc_info()
        formatted_lines = traceback.format_exception(exc_type, value, tb)
        print(f"ERROR in 'do_launch' {''.join(formatted_lines)}")


def do_discussion(
    page: Page,
    browser_info: BrowserInfo,
    action_info: ActionInfo,
    signals: WorkerSignals,
):
    try:
        signals.log_message.emit(
            f"[{browser_info.user_id}] Performing <{action_info.action_name}> action ..."
        )
        group_num = 5

        # Section 1: Get groups
        page.goto("https://www.facebook.com/groups/feed/", timeout=60000)
        page_language = page.locator("html").get_attribute("lang")
        if page_language != "en":
            signals.log_message.emit("Switch to English.")
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
        group_urls = [
            group_locator.get_attribute("href")
            for group_locator in group_locators.all()
        ]
        if not len(group_urls):
            signals.log_message.emit("Could not retrieve any group URLs")
            return
        # Section 2: Published post to group
        current_group = 0
        for group_url in group_urls:
            page.goto(group_url, timeout=60_000)
            main_locator = page.locator(selectors.S_MAIN)
            tablist_locator = main_locator.first.locator(selectors.S_TABLIST)
            try:
                tablist_locator.first.wait_for(state="attached", timeout=5_000)
            except:
                # print(tablist_locator.first.wait_for(state="attached", timeout=5_000))
                # page.wait_for_event("close", timeout=0)
                continue
            tab_locators = tablist_locator.first.locator(selectors.S_TABLIST_TAB)
            is_discussion = False
            for tab_locator in tab_locators.all():
                is_discussion = True
                tab_url = tab_locator.get_attribute("href", timeout=5_000)
                if not tab_url:
                    # print('tab_locator.get_attribute("href", timeout=5_000)')
                    # page.wait_for_event("close", timeout=0)
                    continue
                tab_url = tab_url[:-1] if tab_url.endswith("/") else tab_url
                if tab_url.endswith == "buy_sell_discussion":
                    is_discussion = False
                    break
            if is_discussion:
                profile_locator = main_locator.first.locator(selectors.S_PROFILE)
                try:
                    profile_locator.first.wait_for(state="attached", timeout=60_000)
                except Exception as e:
                    print(e)
                    print(
                        'profile_locator.first.wait_for(state="attached", timeout=60_000)'
                    )
                    page.wait_for_event("close", timeout=0)
                    # continue
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
                try:
                    discussion_btn_locator.first.click()
                except Exception as e:
                    print(e)
                    print("discussion_btn_locator.first.click()")
                    page.wait_for_event("close", timeout=0)
                    # continue

                page.locator(selectors.S_DIALOG_CREATE_POST).first.locator(
                    selectors.S_LOADING
                ).first.wait_for(state="detached", timeout=30_000)
                dialog_locator = page.locator(selectors.S_DIALOG_CREATE_POST)
                dialog_container_locator = dialog_locator.first.locator(
                    "xpath=ancestor::*[contains(@role, 'dialog')][1]"
                )
                if len(action_info.images_path):
                    try:
                        dialog_container_locator.locator(
                            selectors.S_IMG_INPUT
                        ).wait_for(state="attached", timeout=10_000)
                    except PlaywrightTimeoutError:
                        image_btn_locator = dialog_container_locator.first.locator(
                            selectors.S_IMAGE_BUTTON
                        )
                        random_sleep(1, 3)
                        image_btn_locator.click()
                    finally:
                        image_input_locator = dialog_container_locator.locator(
                            selectors.S_IMG_INPUT
                        )
                        random_sleep(1, 3)
                        image_input_locator.set_input_files(
                            action_info.images_path, timeout=10000
                        )
                textbox_locator = dialog_container_locator.first.locator(
                    selectors.S_TEXTBOX
                )
                random_sleep(1, 3)
                textbox_locator.fill(action_info.description)
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
                signals.log_message.emit(f"Published in {group_url}.")
            else:
                continue
            if current_group >= group_num:
                break
            current_group += 1

    except Exception as e:
        print("ERROR: ", e)
        pass


ACTION_MAP = {
    "launch": do_launch,
    "discussion": do_discussion,
}
