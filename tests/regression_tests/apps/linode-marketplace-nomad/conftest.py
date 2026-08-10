import pytest

from regression_tests.services.nomad.nomad_service import NomadService


@pytest.fixture(scope="session")
def credentials_file_path():
    """
    Returns the path to the credentials file on the Nomad provisioner.

    Returns:
        str: Absolute path to the credentials file.
    """
    return "/home/admin/.deployment-secrets.txt"


@pytest.fixture(scope="session")
def base_url(ssh_credentials):
    """
    Constructs the base HTTPS URL for the Nomad UI.

    Args:
        ssh_credentials: host, username, password.

    Returns:
        str: The base URL nginx serves the Nomad UI on.
    """
    host = ssh_credentials[0]
    linode_host = host.replace(".", "-")
    return f"https://{linode_host}.ip.linodeusercontent.com"


@pytest.fixture(scope="session")
def nomad_token(app_credentials):
    """
    Returns the ACL token the deployment creates for day-to-day use. Nomad has no
    username/password login; this Secret ID is what the UI authenticates with.

    Args:
        app_credentials: Parsed credentials file from the provisioner.

    Returns:
        str: The Secret ID of the Nomad user token.
    """
    return app_credentials["nomad_user_token"]


@pytest.fixture(scope="session")
def nomad_service(remote_exec, nomad_token):
    """
    Returns the Nomad service object used by the cluster tests.

    Args:
        remote_exec: Callable running commands on the provisioner over SSH.
        nomad_token: Secret ID used to authenticate API calls.

    Returns:
        NomadService: Service object exposing the cluster's own view of itself.
    """
    return NomadService(remote_exec=remote_exec, token=nomad_token)
