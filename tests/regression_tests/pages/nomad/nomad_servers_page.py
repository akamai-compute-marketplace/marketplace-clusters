from playwright.sync_api import Page

from regression_tests.pages.base_page import BasePage


class NomadServersPage(BasePage):
    PATH = "/ui/servers"

    def __init__(self, page: Page):
        super().__init__(page)
        self.server_rows = self.page.locator("tr.server-agent-row")
        self.status_cells = self.page.locator("tr.server-agent-row td:nth-child(2)")
        self.leader_cells = self.page.locator("tr.server-agent-row td:nth-child(3)")

    def navigate(self, base_url: str):
        super().navigate(f"{base_url}{self.PATH}")
