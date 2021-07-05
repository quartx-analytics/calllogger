# Standard lib
from urllib import parse as urlparse
from typing import Union
import logging
import socket
import time

# Third party
from requests import codes

# Local
from calllogger import settings, __version__, utils, running
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth

info_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/info/")
linking_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/link-device/")
logger = logging.getLogger(__name__)


def get_private_ip() -> str:
    """Return the local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("quartx.ie", 80))
            return s.getsockname()[0]
    except OSError:
        return ""


def get_client_info(token: TokenAuth, identifier: str) -> dict:
    """Request information about the client."""
    api = QuartxAPIHandler()

    # We will pass data to server using query params
    params = dict(
        device_id=identifier,
        version=__version__,
    )

    # Add the local IP address
    if private_ip := get_private_ip():
        params["private_ip"] = private_ip

    resp = api.make_request(
        method="POST",
        url=info_url,
        auth=token,
        json=params,
    )
    client_data = resp.json()
    settings.override(client_data["setting_overrides"])
    return client_data


def link_device(identifier) -> Union[str, None]:
    """Link device to a tenant on the server and return the provided token."""
    logger.info("Registering device with server using identifier: %s", identifier)
    api = QuartxAPIHandler()
    start = time.time()

    while running.is_set():  # pragma: no branch
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
            logger.debug("Device registration rejected. Will try again soon.")
            utils.sleeper(settings.device_reg_check, running.is_set)
            # Keep attempting registration until timeout elapse
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
