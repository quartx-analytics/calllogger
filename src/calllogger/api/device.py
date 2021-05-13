# Standard Lib
import urllib.parse as urlparse

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.conf import settings

linking_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/link-device/")
reg_key = "216543516519684sd564321d86e5432s"


def link_device(identifier: str) -> str:
    """Link device to a tenant on the server and return the provided token."""
    api = QuartxAPIHandler()
    resp = api.make_request(
        method="POST",
        url=linking_url,
        json={
            "device_id": identifier,
            "reg_key": reg_key,
        },
        headers={"content-type": "application/json"},
    )
    # TODO: Change QuartxAPIHandler to not require content-type to be set for json
    return resp.json()["token"]
