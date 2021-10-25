# Standard lib
from urllib.parse import urljoin
from typing import Union
import logging
import time

# Third party
from requests import codes

# Local
from calllogger import settings, __version__, stopped
from calllogger.api import QuartxAPIHandler

linking_url = urljoin(settings.domain, "/api/v1/monitor/cdr/link-device/")
logger = logging.getLogger(__name__)


def link_device(identifier) -> Union[str, None]:
    """Link device to a tenant on the server and return the provided token."""
    logger.info("Registering device with server using identifier: %s", identifier)
    api = QuartxAPIHandler()
    start = time.time()

    while not stopped.is_set():  # pragma: no branch
        resp = api.make_request(
            method="POST",
            url=linking_url,
            json=dict(
                device_id=identifier,
                reg_key=settings.reg_key,
                version=__version__,
            ),
        )
        # Resp may be None if program is shutting down
        status_code = getattr(resp, "status_code", None)
        if status_code == codes["created"]:  # 201
            logger.info("Device token received")
            data = resp.json()
            return data["token"]
        elif status_code == codes["no_content"]:  # 204
            logger.debug("Device registration rejected. Will try again in %s seconds.", settings.device_reg_check)
            stopped.wait(settings.device_reg_check)

            # Keep attempting registration until global timeout elapse
            if time.time() - start < settings.device_reg_timeout:
                continue
            else:
                logger.info("Device registration failed: Registration time elapsed, giving up.")
                return None
        else:
            # Have no idea what to do here only return None
            logger.info(
                "Device registration failed: %s -> %s",
                getattr(resp, "status_code", ""),
                getattr(resp, "reason", "")
            )
            return None
