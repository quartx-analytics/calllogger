# Standard lib
from urllib import parse as urlparse

# Local
from calllogger.conf import settings


def authenticate():
    url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/auth")
