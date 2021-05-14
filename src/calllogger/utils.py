"""
Utility module
--------------
Some useful function this package needs.

This module should never import anything from the calllogger package.
It should be self contained, third party imports are fine.
"""

# Standard Lib
from datetime import datetime
import logging
import base64
import time
import json
import os

logger = logging.getLogger(__name__)


class OnlyMessages(logging.Filter):
    """Filter out log records that are less than the WARNING level."""
    def filter(self, record):
        return record.levelno < logging.WARNING


class ComplexEncoder(json.JSONEncoder):
    """Custom Json Encoder to serialize other types of python objects."""

    def default(self, obj):
        # Decode datetime objects to iso format
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class Timeout:
    """
    A class to handle timeout decay when continuously called.

    When sleep is called, the program will sleep for the required timeout.
    Then the timeout value will be increased by multiplying it by the timeout decay.
    The timeout will be capped to the max timeout setting.

    .. note:
        When your function call has completed successfully the reset
        method neeeds to be called to undo the timeout decay.

    :param settings: Programs settings object.
    :param callback: A callable that should return True/False to state if program is still running.
    """

    def __init__(self, settings, callback: callable):
        self._settings = settings
        self._timeout = settings.timeout
        self._callback = callback

    def sleep(self):
        """Sleep for the required timeout, increasing timeout value before returning."""
        logger.info("Retrying in '%d' seconds", self._timeout)
        sleeper(self._timeout, self._callback)
        self._timeout = int(min(self._settings.max_timeout, self._timeout * self._settings.timeout_decay))

    def reset(self):
        """Reset the timeout value by undoing the timeout decay."""
        if self._timeout != self._settings.timeout:
            logger.info("Everything is working again. Resetting timeout.")
            self._timeout = self._settings.timeout

    @property
    def value(self) -> int:
        return self._timeout


def sleeper(timeout: float, callback: callable):
    """
    Sleep for a given amount of time while checking callback
    every half a second to see if sleeping is still required.
    This allows for the program to gracefully shutdown.
    """
    timeout = timeout * 2
    while timeout > 0 and callback():
        time.sleep(.5)
        timeout -= 1


# TODO: Create tests for this function
def decode_env(env, default="") -> str:
    """Decode a Base64 encoded environment variable."""
    if value := os.environ.get(env, default):
        value = base64.b64decode(value)
    return value
