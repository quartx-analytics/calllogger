# Standard Lib
from typing import Union
import logging
import time
import json

# Third Party
import requests

logger = logging.getLogger(__name__)


class OnlyMessages(logging.Filter):
    """Filter out log records that are less than the WARNING level."""
    def filter(self, record):
        return record.levelno < logging.WARNING


class Timeout:
    """
    A class to handle timeout decay when continuously called.

    When sleep is called, the program will sleep for the required timeout.
    Then the timeout value will be increased by multiplying it by the timeout decay.
    The timeout will be capped to the max timeout setting.

    .. note:
        When your function call has completed successfully
        reset neeeds to be called to undo the timeout decay.
    """

    def __init__(self, settings):
        self._settings = settings
        self._timeout = settings.timeout

    def sleep(self):
        """Sleep for the required timeout, increasing timeout value before returning."""
        logger.info("Retrying in '%d' seconds", self._timeout)
        time.sleep(self._timeout)
        self._timeout = min(self._settings.max_timeout, self._timeout * self._settings.decay)

    def reset(self):
        """Reset the timeout value by undoing the timeout decay."""
        self._timeout = self._settings.timeout

    @property
    def value(self) -> int:
        return self._timeout

    def __int__(self):
        return self._timeout


def decode_response(resp: requests.Response, limit=1000) -> Union[str, dict]:
    """Decode the response body using json if possible else limit body to 1000 characters."""
    try:
        return resp.json()
    except json.decoder.JSONDecodeError:
        logger.debug("Error response was not a valid json response")
        return resp.text[:limit]
