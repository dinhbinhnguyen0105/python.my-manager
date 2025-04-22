import random
from playwright.sync_api import Locator


# def handle_type(
#     locator: Locator, text: str, min_delay: float = 0.1, max_delay: float = 0.5
# ):
#     for char in text:
#         locator.type(char, delay=random.uniform(min_delay, max_delay) * 1000)


def handle_type(
    locator: Locator, text: str, min_delay: float = 0.1, max_delay: float = 0.5
):
    for char in text:
        locator.type(char, delay=random.uniform(min_delay, max_delay) * 500)
