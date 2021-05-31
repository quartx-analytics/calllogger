"""
Utility module
--------------
Some useful function this package needs.

This module should never import anything from the calllogger package.
It should be self contained, third party imports are fine.
"""

# Standard Lib
import threading
import logging
import base64
import time
import os

# Third Party
from requests.auth import AuthBase

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


class TokenAuth(AuthBase):
    """Requests Token authentication class."""

    def __init__(self, token: str):
        self.__token = token

    def __call__(self, req):
        req.headers["Authorization"] = f"Token {self.__token}"
        return req


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


def decode_env(env, default="") -> str:
    """Decode a Base64 encoded environment variable."""
    encode_check = "ZW5jb2RlZDo="
    value = os.environ.get(env, default)
    if value and value.startswith(encode_check):
        value = value[len(encode_check):]
        value = base64.b64decode(value).decode("utf8")
    return value


class ExitCodeManager:
    """
    Manager to keep track of the exit code on running threads.

    Will only allow for the exit code to be set once.
    Any other attempt to set the exit code will be ignored.

    This is needed so a thread can trigger the program to exit and
    have the thread state the exit code. Docker will then restart the
    program if the exit code is anything other than 0.
    """

    def __init__(self):
        self.lock = threading.Lock()
        # Exit code of zero says that the program
        # exited gracefully (Linux Default)
        self.__exit_code = self.__set = None
        self.reset()

    def reset(self):
        """Reset to defaults."""
        self.__exit_code = 0
        self.__set = False

    def set(self, exit_code: int):
        """Set the exit code."""
        if self.__set is False:
            with self.lock:
                self.__exit_code = exit_code
                self.__set = True

    def value(self) -> int:
        """Return the exit code and reset."""
        return self.__exit_code
