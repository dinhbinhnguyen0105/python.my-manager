import random, traceback, sys
from time import sleep
from PyQt6.QtCore import QObject, pyqtSignal
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from typing import Tuple
from src.robot import selectors
from src.my_types import BrowserInfo, ActionInfo, TaskInfo

MIN = 60_000


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
        # [56]
        # [58] Preparing ...
        # [55] Preparing ...
        # [54] Preparing ...
        # page.goto("https://www.facebook.com", timeout=60000)
        # page.goto("https://bot.sannysoft.com/", timeout=60000)
        signals.log_message.emit(f"[{browser_info.user_id}] Wait for closing ...")
        page.wait_for_event("close", timeout=0)
        signals.log_message.emit(f"[{browser_info.user_id}] Closed!")
        return True
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
        group_num = 9

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
            page.goto(group_url, timeout=MIN)
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
                    profile_locator.first.wait_for(state="attached", timeout=MIN)
                except Exception as e:
                    print(e)
                    print(
                        'profile_locator.first.wait_for(state="attached", timeout=MIN)'
                    )
                    # page.wait_for_event("close", timeout=0)
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
                try:
                    discussion_btn_locator.first.click()
                except Exception as e:
                    print(e)
                    print("discussion_btn_locator.first.click()")
                    # page.wait_for_event("close", timeout=0)
                    continue

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
                dialog_container_locator.wait_for(state="detached", timeout=MIN)
                random_sleep(1, 3)
                signals.log_message.emit(f"Published in {group_url}.")
            else:
                continue
            if current_group >= group_num:
                break
            current_group += 1
        sleep(30)

    except Exception as e:
        print("ERROR: ", e)
        pass


def do_marketplace(
    page: Page,
    browser_info: BrowserInfo,
    action_info: ActionInfo,
    signals: WorkerSignals,
):
    try:
        signals.log_message.emit(
            f"[{browser_info.user_id}] Performing <{action_info.action_name}> action ..."
        )

        page.goto("https://www.facebook.com/marketplace/create/item", timeout=60000)
        page_language = page.locator("html").get_attribute("lang")
        if page_language != "en":
            signals.log_message.emit("Switch to English.")
            return
        marketplace_forms = page.locator(selectors.S_MARKETPLACE_FORM)
        marketplace_form = None
        for marketplace_form in marketplace_forms.all():
            if marketplace_form.is_visible() and marketplace_form.is_enabled():
                break
        if not marketplace_form:
            error_msg = (
                f"{selectors.S_MARKETPLACE_FORM} is not found or is not interaction."
            )
            print(error_msg)
            signals.log_message.emit(error_msg)
            return False

        close_dialog(page)
        expand_btn_locators = marketplace_form.locator(selectors.S_EXPAND_BUTTON)
        sleep(random.uniform(0.2, 1.5))
        expand_btn_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        expand_btn_locators.first.click(timeout=MIN)

        description_locators = marketplace_form.locator(selectors.S_TEXTAREA)
        sleep(random.uniform(0.2, 1.5))
        description_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        description_locators.first.fill(value=action_info.description, timeout=MIN)

        input_text_locators = marketplace_form.locator(selectors.S_INPUT_TEXT)
        title_locator = input_text_locators.nth(0)
        price_locator = input_text_locators.nth(1)
        location_locator = input_text_locators.nth(3)

        sleep(random.uniform(0.2, 1.5))
        title_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        title_locator.fill(value=action_info.title, timeout=MIN)
        sleep(random.uniform(0.2, 1.5))
        price_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        price_locator.fill(value="0", timeout=MIN)
        sleep(random.uniform(0.2, 1.5))

        location_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        location_locator.fill("Đà Lạt")
        location_locator.press(" ")
        location_listbox_locators = page.locator(selectors.S_UL_LISTBOX)
        sleep(random.uniform(0.2, 1.5))
        location_listbox_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        location_listbox_locators.first.wait_for(state="attached", timeout=MIN)
        location_option_locators = location_listbox_locators.first.locator(
            selectors.S_LI_OPTION
        )
        sleep(random.uniform(0.2, 1.5))
        location_option_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        location_option_locators.first.click(timeout=MIN)

        combobox_locators = page.locator(selectors.S_LABEL_COMBOBOX_LISTBOX)
        category_locator = combobox_locators.nth(0)
        condition_locator = combobox_locators.nth(1)

        sleep(random.uniform(0.2, 1.5))
        category_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        category_locator.click(timeout=MIN)

        dialog_locators = page.locator(selectors.S_DIALOG_DROPDOWN)
        dialog_locators.first.wait_for(state="attached", timeout=MIN)
        dialog_button_locators = dialog_locators.first.locator(selectors.S_BUTTON)
        dialog_misc_button_locator = dialog_button_locators.nth(
            dialog_button_locators.count() - 2
        )
        sleep(random.uniform(0.2, 1.5))
        dialog_misc_button_locator.scroll_into_view_if_needed()
        dialog_misc_button_locator.click(timeout=MIN)
        dialog_locators.wait_for(state="detached")

        sleep(random.uniform(0.2, 1.5))
        condition_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        condition_locator.click(timeout=MIN)
        listbox_locators = page.locator(selectors.S_DIV_LISTBOX)
        listbox_locators.first.wait_for(state="attached", timeout=MIN)
        listbox_option_locators = listbox_locators.first.locator(selectors.S_DIV_OPTION)

        sleep(random.uniform(0.2, 1.5))
        listbox_option_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        listbox_option_locators.first.click(timeout=MIN)
        dialog_locators.wait_for(state="detached")

        image_input_locators = marketplace_form.locator(selectors.S_IMG_INPUT)
        sleep(random.uniform(0.2, 1.5))
        image_input_locators.first.set_input_files(action_info.images_path)

        is_closed_dialog = False
        page.locator(selectors.S_NEXT_BUTTON).wait_for(state="attached", timeout=MIN)
        next_btn_locators = page.locator(selectors.S_NEXT_BUTTON)
        try:
            sleep(random.uniform(0.2, 1.5))
            next_btn_locators.first.click(timeout=MIN)
            is_closed_dialog = True
        except PlaywrightTimeoutError:
            is_closed_dialog = close_dialog(page)
        if not is_closed_dialog:
            raise Exception("Cannot close anonymous dialog!")
        sleep(random.uniform(0.2, 1.5))

        checkbox_locators = marketplace_form.locator(selectors.S_CHECK_BOX)
        for checkbox_locator in checkbox_locators.all():
            if checkbox_locator.is_visible() and checkbox_locator.is_enabled():
                sleep(random.uniform(0.2, 0.8))
                checkbox_locator.scroll_into_view_if_needed()
                sleep(random.uniform(0.2, 0.8))
                checkbox_locator.click()

        page.locator(selectors.S_PUBLISH_BUTTON).wait_for(state="attached", timeout=MIN)
        publish_btn_locators = page.locator(selectors.S_PUBLISH_BUTTON)
        try:
            sleep(random.uniform(0.2, 1.5))
            publish_btn_locators.first.click(timeout=MIN)
            is_closed_dialog = True
        except PlaywrightTimeoutError:
            is_closed_dialog = close_dialog(page)
        if not is_closed_dialog:
            raise Exception("Cannot close anonymous dialog!")
        sleep(random.uniform(0.2, 1.5))
        publish_btn_locators = page.locator(selectors.S_PUBLISH_BUTTON)
        for publish_btn_locator in publish_btn_locators.all():
            if publish_btn_locator.is_enabled() and publish_btn_locator.is_visible():
                sleep(random.uniform(0.2, 0.8))
                publish_btn_locator.click()
                break
        sleep(30)
        return True
    except Exception as e:
        print("ERROR: ", e)
        # page.wait_for_event("close", timeout=0)

        return
        pass
        # tablist_locator.first.wait_for(state="attached", timeout=5_000)


def close_dialog(page: Page):
    try:
        dialog_locators = page.locator(selectors.S_DIALOG)
        for dialog_locator in dialog_locators.all():
            if dialog_locator.is_visible() and dialog_locator.is_enabled():
                close_button_locators = dialog_locator.locator(selectors.S_CLOSE_BUTTON)
                sleep(random.uniform(0.2, 1.5))
                close_button_locators.last.click(timeout=MIN)
                dialog_locator.wait_for(state="detached", timeout=MIN)
        return True
    except PlaywrightTimeoutError:
        return False


ACTION_MAP = {
    "launch": do_launch,
    "discussion": do_discussion,
    "marketplace": do_marketplace,
}
