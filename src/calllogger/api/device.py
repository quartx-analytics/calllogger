# Standard Lib
import urllib.parse as urlparse

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.conf import settings

linking_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/link-device/")


def link_device(identifier) -> str:
    """Link device to a tenant on the server and return the provided token."""
    api = QuartxAPIHandler()
    resp = api.make_request(
        method="POST",
        url=linking_url,
        json={
            "device_id": identifier,
            "reg_key": settings.reg_key,
        }
    )
    return resp.json()["token"]
