from __future__ import annotations

# Standard lib
from urllib.parse import urljoin
from typing import Optional
import logging
import socket
import os

# Third party
import sentry_sdk
import uptime
import psutil

# Local
from calllogger import settings, stopped, __version__
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth
from calllogger.misc import ThreadTimer

info_url = urljoin(settings.domain, "/api/v1/monitor/cdr/info/")
root_logger = logging.getLogger("calllogger")
logger = logging.getLogger(__name__)


class ClientInfo:
    """Class to make accessing client data easier."""

    def __init__(self, raw_json: dict):
        self.__dict__["raw_json"] = raw_json

    def __setattr__(self, name, value):
        raise Exception("Attribute is Read-Only")

    def __getattr__(self, name):
        try:
            return self.raw_json[name]
        except KeyError:
            raise AttributeError("'{0}' object has no attribute '{1}'".format(self.__class__.__name__, name))

    def __getitem__(self, key):
        return self.raw_json[key]

    @classmethod
    def get_client_info(cls, token: TokenAuth, identifier: str, checkin=False) -> ClientInfo:
        """Request information about the client."""
        (logger.debug if checkin else logger.info)("Requesting client info and settings")
        api = QuartxAPIHandler()
        api.logger = logger

        # We will pass data to server using query params
        params = dict(
            device_id=identifier,
            version=__version__,
        )

        # Report the current system uptime
        uptime_in_sec = uptime.uptime()
        if uptime_in_sec is not None:
            params["uptime"] = int(uptime_in_sec)

        # Add the local IP address
        if private_ip := get_private_ip():
            params["private_ip"] = private_ip

        # Add the zerotier IP address
        if zerotier_ip := get_zerotier_ip():
            params["zerotier_ip"] = zerotier_ip

        resp = api.make_request(
            method="POST",
            url=info_url,
            auth=token,
            json=params,
        )

        client_data = resp.json()
        client_data = cls(client_data)

        # Check if a restart is requested
        if checkin and client_data.restart:
            logger.info("Restart was requested. Restarting...")
            # By setting this flag, it will cause the whole program to exit
            # Exit code of 1 is needed to trigger the restart
            stopped.set(1)

        # Update settings
        update_settings(**client_data.settings)

        # Update sentry user
        set_sentry_user(client_data)
        return client_data

    @classmethod
    def setup_checkin(cls, token: TokenAuth, identifier: str):
        logger.info("Scheduling client checkin for every 30min")
        ThreadTimer(
            # Convert from minutes to seconds
            settings.checkin_interval * 60,
            cls.get_client_info,
            args=[token, identifier],
            kwargs={"checkin": True},
            repeat=True
        ).start()


def set_sentry_user(client_info: ClientInfo):
    """Setup sentry user using client info."""
    sentry_sdk.set_user({
        "id": client_info.id,
        "username": client_info.name,
        "email": client_info.email,
    })


def get_private_ip() -> str:
    """Return the local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("quartx.ie", 80))
            return sock.getsockname()[0]
    except OSError:
        return ""


# noinspection PyBroadException
def get_zerotier_ip() -> Optional[str]:
    """Return the IP address of the zerotier private network."""
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            if interface.startswith("zt"):
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        return addr.address
    except Exception:
        logger.error("Unable to extract zerotier IP address")
        return None


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
