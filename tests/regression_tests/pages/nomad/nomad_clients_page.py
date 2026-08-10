from playwright.sync_api import Page

from regression_tests.pages.base_page import BasePage


class NomadClientsPage(BasePage):
    PATH = "/ui/clients"

    def __init__(self, page: Page):
        super().__init__(page)
        self.client_rows = self.page.locator("tr.client-node-row")
        self.state_cells = self.page.locator("tr.client-node-row td:nth-child(4)")

    def navigate(self, base_url: str):
        super().navigate(f"{base_url}{self.PATH}")
