# Standard Lib
import logging
import time

logger = logging.getLogger(__name__)


class OnlyMessages(logging.Filter):
    """Filter out records that are less than the WARNING level."""
    def filter(self, record):
        return record.levelno < logging.WARNING


class Timeout:
    """
    A class to handle timeout decay when continuously called.

    When sleep is called, the program will sleep for the required timeout.
    Then the timeout value will be increased by multiplying it by the timeout decay.
    The timeout will be capped to the max timeout setting.

    .. note:
        When your function call has completed successfully,
        reset neeeds to be called to undo the timeout decay.
    """

    def __init__(self, settings):
        self._settings = settings
        self._timeout = settings.TIMEOUT

    @property
    def value(self):
        return self._timeout

    def sleep(self):
        """Sleep for the required timeout, increasing timeout value before returning."""
        logger.info(f"Retrying in {self._timeout} seconds")
        time.sleep(self._timeout)
        self._timeout = min(self._settings.MAX_TIMEOUT, self._timeout * self._settings.DECAY)

    def reset(self):
        """Reset the timeout value by undoing the timeout decay."""
        self._timeout = self._settings.TIMEOUT
