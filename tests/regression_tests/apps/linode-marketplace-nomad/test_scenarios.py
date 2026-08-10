from playwright.sync_api import expect

from regression_tests.pages.nomad.nomad_clients_page import NomadClientsPage
from regression_tests.pages.nomad.nomad_jobs_page import NomadJobsPage
from regression_tests.pages.nomad.nomad_login_page import NomadLoginPage
from regression_tests.pages.nomad.nomad_servers_page import NomadServersPage

EXPECTED_SERVER_COUNT = 3
EXPECTED_CLIENT_COUNT = 3
CLIENT_READY_STATE = "Ready Eligible Not Draining"
SMOKE_JOB_ID = "ui-regression-smoke"


def sign_in(context, base_url, nomad_token):
    login_page = NomadLoginPage(context)
    login_page.navigate(base_url)
    login_page.sign_in(nomad_token)


def test_nomad_startup(context, base_url):
    # Verifies that nginx serves the Nomad UI and the application shell renders.
    jobs_page = NomadJobsPage(context)
    jobs_page.navigate(base_url)

    expect(context, "The Nomad UI did not start.").to_have_title("Jobs - Nomad")


def test_nomad_ui_requires_a_token(context, base_url):
    # Verifies that ACLs are enforced. This cluster has no login form, so an
    # unauthenticated visitor must be refused the cluster's contents.
    jobs_page = NomadJobsPage(context)
    jobs_page.navigate(base_url)

    expect(
        jobs_page.not_authorized_heading,
        "The job list rendered without a token - ACLs are not being enforced.",
    ).to_be_visible()


def test_nomad_sign_in_with_token(context, base_url, nomad_token):
    # Verifies that the token the deployment generated is accepted by the UI.
    login_page = NomadLoginPage(context)
    login_page.navigate(base_url)
    login_page.sign_in(nomad_token)

    expect(
        login_page.authenticated_alert,
        "The deployment's Nomad token was not accepted by the UI.",
    ).to_be_visible()


def test_nomad_all_servers_registered_with_one_leader(context, base_url, nomad_token):
    # Verifies that every server joined and that raft elected exactly one leader,
    # which is what separates a real quorum from three isolated servers.
    sign_in(context, base_url, nomad_token)

    servers_page = NomadServersPage(context)
    servers_page.navigate(base_url)

    expect(
        servers_page.status_cells, "Not every Nomad server is alive."
    ).to_have_text(["Alive"] * EXPECTED_SERVER_COUNT)
    expect(
        servers_page.leader_cells.filter(has_text="True"),
        "The cluster does not have exactly one leader.",
    ).to_have_count(1)


def test_nomad_all_clients_are_ready(context, base_url, nomad_token):
    # Verifies that every client registered with the servers and is schedulable.
    sign_in(context, base_url, nomad_token)

    clients_page = NomadClientsPage(context)
    clients_page.navigate(base_url)

    expect(
        clients_page.state_cells,
        "Not every Nomad client is ready and eligible for scheduling.",
    ).to_have_text([CLIENT_READY_STATE] * EXPECTED_CLIENT_COUNT)


def test_nomad_job_runs_across_the_cluster(context, base_url, nomad_token, nomad_service):
    # Verifies that a real workload is accepted, placed on every client and runs to
    # completion. distinct_hosts forces one allocation per client, so a cluster that
    # looks healthy but cannot schedule across its nodes fails here.
    result = nomad_service.run_smoke_job(
        job_id=SMOKE_JOB_ID, count=EXPECTED_CLIENT_COUNT
    )

    assert result["client_statuses"] == ["complete"] * EXPECTED_CLIENT_COUNT, (
        f"Allocations ended as {result['client_statuses'] or 'nothing was placed'}, "
        f"expected all complete. Submit output:\n{result['submit_output'][-1000:]}"
    )
    assert len(result["node_ids"]) == EXPECTED_CLIENT_COUNT, (
        f"The job ran on {len(result['node_ids'])} client(s); "
        f"expected it to spread across all {EXPECTED_CLIENT_COUNT}."
    )

    sign_in(context, base_url, nomad_token)

    jobs_page = NomadJobsPage(context)
    jobs_page.navigate(base_url)
    expect(
        jobs_page.job_status(SMOKE_JOB_ID),
        f"The UI does not report {SMOKE_JOB_ID} as complete.",
    ).to_have_text("Complete")
