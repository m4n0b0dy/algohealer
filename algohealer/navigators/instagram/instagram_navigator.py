from typing import Optional

from algohealer.navigators.base.social_media_navigator import SocialMediaNavigator


class InstagramNavigator(SocialMediaNavigator):
    name = "instagram"
    url_base = "https://www.instagram.com"

    login_subpage = "accounts/login/"
    username_input = 'input[name="username"]'
    password_input = 'input[name="password"]'
    login_button = 'button[type="submit"]'
    next_button = 'svg[aria-label="Next"]'
    previous_button = 'svg[aria-label="Previous"]'
    like_button = 'svg[aria-label="Like"]'
    unlike_button = 'svg[aria-label="Unlike"]'
    follow_button = 'button > div > div:has-text("Follow")'
    following_button = 'button > div > div:has-text("Following")'
    unfollow_button = 'span > span:has-text("Unfollow")'
    first_post = "div > div > a > div > div > img"
    comment_button = 'svg[aria-label="Comment"]'
    comment_textarea = 'div > textarea[aria-label="Add a comment..."]'
    post_comment_button = 'div > div > div:has-text("Post")'
    search_button = 'svg[aria-label="Search"]'
    search_input = 'input[aria-label="Search input"]'
    search_result = 'div > div > span:has-text("{}")'

    def __init__(self, *args, **kwargs):
        super().__init__(
            nav_name=InstagramNavigator.name,
            url_base=InstagramNavigator.url_base,
            *args,
            **kwargs,
        )

    def login(self, username: str, password: str):
        self.load_subpage(self.login_subpage)
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.wait_check_click(self.login_button)

    def next_content(self) -> bool:
        return self.wait_check_click(self.next_button)

    def previous_content(self):
        return self.wait_check_click(self.previous_button)

    def like_content(self) -> bool:
        cl = self.wait_check_click(self.like_button)
        if not cl:
            return cl
        return self.wait_check_click(self.like_button)

    def unlike_content(self):
        return self.wait_check_click(self.unlike_button)

    def follow_account(self):
        return self.wait_check_click(self.follow_button)

    def unfollow_account(self):
        self.wait_check_click(self.following_button)
        return self.wait_check_click(self.unfollow_button)

    def open_first_post(self) -> bool:
        return self.wait_check_click(self.first_post)

    def comment(self, text: str) -> bool:
        cl = self.wait_check_click(self.comment_button)
        if not cl:
            return cl
        cl = self.wait_then_fill(self.comment_textarea, text)
        if not cl:
            return cl
        return self.wait_check_click(self.post_comment_button)

    def search(self, query: str, result: Optional[str] = None, *args, **kwargs) -> bool:
        if not result:
            result = query

        cl = self.wait_check_click(self.search_button)
        if not cl:
            return cl
        self.wait_then_fill(self.search_input, query)
        return self.wait_check_click(self.search_result.format(result))

    def like_new_posts(self, max_posts: int = 10):
        pages = self.get_current_account_names()
        for page in pages:
            self.load_subpage(page)
            clicked = self.open_first_post()
            if not clicked:
                continue

            for _ in range(max_posts):
                self.random_sleep(1, 2)
                cl = self.next_content()
                if not cl:
                    break

    def run(self):
        self.like_new_posts()
