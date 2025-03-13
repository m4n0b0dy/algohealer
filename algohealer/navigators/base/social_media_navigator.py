import os
import random
import time
from typing import List

from playwright._impl._errors import TargetClosedError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from algohealer.db.conn import SQLiteManager


class SocialMediaNavigator:
    def __init__(
        self,
        user_data_dir: str,
        channel: str,
        nav_name: str,
        url_base: str,
        db_conn: SQLiteManager,
        headless: bool = True,
        args: List[str] = [],
    ):
        self._db_conn = db_conn
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel=channel,
                args=args,
                headless=headless,
            )
        except TargetClosedError:
            self._playwright.stop()
            raise TargetClosedError
        self._page = self._browser.new_page()
        self._url_base = self._clean_base_url(url_base)
        self._nav_name = nav_name
        self.load(self._url_base)

    @staticmethod
    def _clean_base_url(url: str):
        if url[-1] == "/":
            url = url[:-1]
        return url

    def stop(self):
        self._browser.close()
        self._playwright.stop()

    def run(self):
        raise NotImplementedError

    def load(self, url: str):
        self._page.goto(url)

    def load_subpage(self, subpage: str):
        self.load(os.path.join(self._url_base, subpage))

    def click(self, selector: str):
        self._page.click(selector)

    def fill(self, selector: str, text: str):
        self._page.fill(selector, text)

    def wait(self, selector: str, timeout: int = 1000) -> bool:
        try:
            self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def wait_check_click(self, selector: str, timeout: int = 1000) -> bool:
        if self.wait(selector=selector, timeout=timeout):
            self.click(selector=selector)
            return True
        return False

    def wait_then_fill(self, selector: str, text: str, timeout: int = 10000):
        self.wait(selector=selector, timeout=timeout)
        self.fill(selector=selector, text=text)

    def press_down(self):
        self._page.keyboard.press("ArrowDown")

    def press_up(self):
        self._page.keyboard.press("ArrowUp")

    def _scroll(self, direction: str, pixels: int = 500):
        if direction not in ["up", "down"]:
            raise ValueError("Scroll direction must be either 'up' or 'down'")
        if direction == "up":
            self._page.evaluate(f"window.scrollBy(0, -{pixels})")
        elif direction == "down":
            self._page.evaluate(f"window.scrollBy(0, {pixels})")

    def scroll_up(self, pixels: int = 500):
        self._scroll(direction="up", pixels=pixels)

    def scroll_down(self, pixels: int = 500):
        self._scroll(direction="down", pixels=pixels)

    @staticmethod
    def sleep(seconds: int):
        time.sleep(seconds)

    @staticmethod
    def random_sleep(min: int, max: int):
        time.sleep(random.uniform(min, max))

    def get_current_account_names(self) -> List[str]:
        accounts = self._db_conn.get_all_accounts_for_site(self._nav_name)
        return [account["name"] for account in accounts]
