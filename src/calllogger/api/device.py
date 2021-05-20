# Standard Lib
import urllib.parse as urlparse
from typing import Union
import logging
import time

# Third party
from requests import codes

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.conf import settings
from calllogger import utils, running

linking_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/link-device/")
logger = logging.getLogger(__name__)


def link_device(identifier) -> Union[str, None]:
    """Link device to a tenant on the server and return the provided token."""
    api = QuartxAPIHandler()
    start = time.time()

    while True:
        resp = api.make_request(
            method="POST",
            url=linking_url,
            json={
                "device_id": identifier,
                "reg_key": settings.reg_key,
            }
        )
        if resp.status_code == codes["created"]:  # 201
            data = resp.json()
            return data["token"]
        elif resp.status_code == codes["no_content"]:  # 204
            logger.debug("Device registration rejected. Will try again soon.")
            utils.sleeper(settings.device_reg_check, running.is_set)
            # Keep attempting registration until timeout elapse
            if time.time() - start < settings.device_reg_timeout:
                continue
            else:
                logger.info(f"Device registration failed: Registration time elapsed, giving up.")
                return None
        else:
            # Have no idea what to do here only return None
            logger.info(f"Device registration failed: {resp.status_code} -> {resp.reason}")
            return None
