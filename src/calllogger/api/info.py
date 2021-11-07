# Standard lib
from urllib.parse import urljoin
import logging
import socket
import os

# Third party
import sentry_sdk

# Local
from calllogger import settings, stopped, __version__
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth
from calllogger.misc import ThreadTimer

info_url = urljoin(settings.domain, "/api/v1/monitor/cdr/info/")
root_logger = logging.getLogger("calllogger")
logger = logging.getLogger(__name__)


def set_sentry_user(client_info: dict):
    """Setup sentry user using client info."""
    sentry_sdk.set_user({
        "id": client_info["id"],
        "username": client_info["name"],
        "email": client_info["email"],
    })


def get_private_ip() -> str:
    """Return the local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("quartx.ie", 80))
            return s.getsockname()[0]
    except OSError:
        return ""


def update_settings(**overrides):
    """
    Override settings that have not been set from an environment variable.
    Environment variables retain highest priority.

    :key overrides: Dict of settings to override.
    """
    for key, val in overrides.items():
        env_key = key.upper()
        # Env must not exist for this setting
        if env_key not in os.environ:
            setattr(settings, key, val)

    # Update logging level
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)


def get_client_info(token: TokenAuth, identifier: str, checkin=False) -> dict:
    """Request information about the client."""
    logger.info("Requesting client info and settings")
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

    # Check if a restart is requested
    if checkin and client_data["restart"]:
        logger.info("Restart was requested. Restarting...")
        # By setting this flag, it will cause the whole program to exit
        # Exit code of 1 is needed to trigger the restart
        stopped.set(1)

    # Update settings
    update_settings(**client_data.get("settings", {}))

    # Update sentry user
    set_sentry_user(client_data)
    return client_data


def setup_client_checkin(token: TokenAuth, identifier: str):
    logger.info("Scheduling client checkin for every 30min")
    ThreadTimer(
        30 * 60,  # 30mins
        get_client_info,
        args=[token, identifier],
        kwargs={"checkin": True},
        repeat=True
    ).start()
