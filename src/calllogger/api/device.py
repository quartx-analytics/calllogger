# Standard Lib
import urllib.parse as urlparse
import base64
import os

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.conf import settings

linking_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/link-device/")
reg_key = base64.b64encode(os.environ.get("LINKED", ""), )


"""
DATASTORE 9B*cDsQfb4AENqgwJYD%W8xL7qDV@qBpMs9xAArn2Y%soQzzS7
LINKKEY e3PyfnX^&*gd&6LJiGtBx3&&Nggvv8x7QQcWrxoRdSUM*QuJi8
"""




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
