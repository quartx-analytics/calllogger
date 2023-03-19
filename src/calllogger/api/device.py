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
    logger.info("Registering device with call monitoring server")
    api = QuartxAPIHandler()
    start = time.time()
    api.logger = logger
    wait_time = settings.device_reg_check

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
            # Switch to long delay mode if device registration period as passed
            if wait_time == settings.device_reg_check and time.time() - start > settings.device_reg_timeout:
                logger.info(
                    "Registration time elapsed. Switching to long delay mode.",
                    extra={"wait_time": settings.device_long_delay},
                )
                wait_time = settings.device_long_delay

            logger.debug("Device registration rejected. Will try again later", extra={"wait_time": wait_time})
            stopped.wait(wait_time)
            continue

        else:
            # Have no idea what to do here only return None
            logger.warning(
                "Device registration failed",
                extra={
                    "status_code": status_code,
                    "reason": getattr(resp, "reason", ""),
                },
            )
            return None
    return None
