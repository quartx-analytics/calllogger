# Standard lib
from threading import Event
from urllib import parse as urlparse

# Local
from calllogger.conf import settings, TokenAuth
from calllogger.api import QuartxAPIHandler

info_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/info")


def get_owner_info(running: Event, token: TokenAuth) -> dict:
    api = QuartxAPIHandler(running)
    resp = api.make_request(
        method="GET",
        url=info_url,
        auth=token,
    )
    return resp.json()