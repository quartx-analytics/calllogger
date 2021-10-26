"""
Utility module
--------------
Some useful function this package needs.

This module should never import anything from the calllogger package.
It should be self contained, third party imports are fine.
"""

# Standard Lib
from pathlib import PosixPath
import threading
import logging
import base64

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
    :param stopped: The stopped event flag state if program is stopped or running.
    """

    def __init__(self, settings, stopped: threading.Event):
        self._settings = settings
        self._timeout = settings.timeout
        self._stopped = stopped
        self._temp_delay = None

    def sleep(self):
        """Sleep for the required timeout, increasing timeout value before returning."""
        logger.info("Retrying in '%d' seconds", self._timeout)
        self._stopped.wait(self.value)
        self._timeout = int(min(self._settings.max_timeout, self._timeout * self._settings.timeout_decay))
        self._temp_delay = None

    def reset(self):
        """Reset the timeout value by undoing the timeout decay."""
        self._timeout = self._settings.timeout
        self._temp_delay = None

    @property
    def value(self) -> int:
        return self._temp_delay or self._timeout

    @value.setter
    def value(self, value: int):
        """Only allow user to change the timeout once. Will reset after."""
        self._temp_delay = value


class TokenAuth(AuthBase):
    """Requests Token authentication class."""

    def __init__(self, token: str):
        self.token = token

    def __call__(self, req):
        req.headers["Authorization"] = f"Token {self.token}"
        return req


class ExitCodeEvent(threading.Event):
    """
    Same as threading.Event but with support for setting a exit_code.

    example::

        >>> stopped = ExitCodeEvent()
        >>> stopped.set(3)  # set event flag with exit code
        >>> print(stopped.get_exit_code())
        3
    """

    def __init__(self):
        super(ExitCodeEvent, self).__init__()
        # Exit code of zero says that the program
        # exited gracefully (Linux Default)
        self.__exit_code = 0

    # noinspection PyUnresolvedReferences
    def set(self, exit_code: int = 0):
        """Set the internal flag to true with program exit code."""
        if not self._flag:
            with self._cond:
                self.__exit_code = exit_code

        # Trigger the real event
        super(ExitCodeEvent, self).set()

    def clear(self):
        """Reset the internal flag exit code."""
        # noinspection PyUnresolvedReferences
        with self._cond:
            self.__exit_code = 0
        super(ExitCodeEvent, self).clear()

    def get_exit_code(self):
        return self.__exit_code


def read_datastore(path: PosixPath, encoding="UTF8") -> str:
    """Decode stored data and return."""
    with path.open("rb") as stream:
        encoded_data = stream.read()
        decoded_data = base64.b64decode(encoded_data)
        return decoded_data.decode(encoding)


def write_datastore(path: PosixPath, data: str, encoding="UTF8"):
    """Encode data and save to disk."""
    with path.open("wb") as stream:
        decoded_data = data.encode(encoding)
        encoded_data = base64.b64encode(decoded_data)
        stream.write(encoded_data)
