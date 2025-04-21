from PyQt6.QtCore import QObject
from playwright.sync_api import Page
from src.utils.logger import log


def do_launch_action(page: Page, user_id, action_info: dict, worker: QObject):
    log(f"User {user_id}: Performing launch action.")
    try:
        page.wait_for_event("close", timeout=0)
        log(f"User {user_id}: Launch action completed.")
        worker.signal_status.emit(user_id, f"User {user_id}: Browser launched.", worker)
    except Exception as e:
        log(f"User {user_id}: Launch action failed: {e}")


def do_discussion_action():
    pass


ACTION_MAP = {
    "launch": do_launch_action,
    "discussion": do_discussion_action,
}
