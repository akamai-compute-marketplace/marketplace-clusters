from playwright.sync_api import Page

from regression_tests.pages.base_page import BasePage


class NomadLoginPage(BasePage):
    """
    Nomad has no username/password form. An unauthenticated visitor is already
    treated as signed in under the anonymous token, so the token form is only
    reachable after signing that session out.
    """

    PATH = "/ui/settings/tokens"

    def __init__(self, page: Page):
        super().__init__(page)
        self.profile_section = self.page.locator("section.authorization-page")
        self.sign_out_button = self.profile_section.get_by_role("button", name="Sign Out")
        self.token_input = self.page.locator("#token-input")
        self.sign_in_button = self.page.get_by_role("button", name="Sign in with secret")
        self.authenticated_alert = self.page.get_by_role("alert").filter(
            has_text="Token Authenticated!"
        )

    def navigate(self, base_url: str):
        super().navigate(f"{base_url}{self.PATH}")

    def sign_in(self, secret_id: str):
        self.sign_out_button.click()
        self.token_input.fill(secret_id)
        self.sign_in_button.click()
        # Nomad stores the token only once it has validated it. Navigating before
        # that confirmation lands cancels the request and leaves the session anonymous.
        self.authenticated_alert.wait_for()
