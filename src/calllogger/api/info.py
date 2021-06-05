# Standard lib
from urllib import parse as urlparse
import socket

# Local
from calllogger import settings, __version__
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth

info_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/info/")


def get_local_ip() -> str:
    """Return the local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("quartx.ie", 80))
            return s.getsockname()[0]
    except OSError:
        return ""


def get_client_info(token: TokenAuth, identifier) -> dict:
    """Request information about the client."""
    api = QuartxAPIHandler()

    # We will pass data to server using query params
    params = dict(
        version=__version__
    )

    # Add identifier as query parameter
    if identifier:
        params["device_id"] = identifier

    # Add the local IP address
    if local_ip := get_local_ip():  # pragma: no branch
        params["local_ip"] = local_ip

    resp = api.make_request(
        method="GET",
        url=info_url,
        auth=token,
        params=params,
    )
    return resp.json()
