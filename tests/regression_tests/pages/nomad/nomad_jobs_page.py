from playwright.sync_api import Page

from regression_tests.pages.base_page import BasePage


class NomadJobsPage(BasePage):
    PATH = "/ui/jobs"

    def __init__(self, page: Page):
        super().__init__(page)
        self.job_rows = self.page.locator("tr.job-row")
        self.not_authorized_heading = self.page.get_by_role(
            "heading", name="Not Authorized"
        )

    def navigate(self, base_url: str):
        super().navigate(f"{base_url}{self.PATH}")

    def job_row(self, job_id: str):
        return self.job_rows.filter(has_text=job_id)

    def job_status(self, job_id: str):
        return self.job_row(job_id).locator("td:nth-child(2)")
