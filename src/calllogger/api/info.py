# Standard lib
from urllib import parse as urlparse

# Local
from calllogger import settings
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth

info_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/info/")


def get_owner_info(token: TokenAuth, identifier) -> dict:
    """Request information about the client."""
    api = QuartxAPIHandler()
    params = {}

    # Add identifier as query parameter
    if identifier:
        params["device_id"] = str(identifier)

    resp = api.make_request(
        method="GET",
        url=info_url,
        auth=token,
        params=params,
    )
    return resp.json()
