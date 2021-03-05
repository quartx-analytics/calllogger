# Standard Lib
import logging
import time

logger = logging.getLogger(__name__)


class OnlyMessages(logging.Filter):
    """Filter out records that are less than the WARNING level."""
    def filter(self, record):
        return record.levelno < logging.WARNING


class Timeout:
    def __init__(self, settings):
        self._max_timeout = settings.MAX_TIMEOUT
        self._org_timeout = settings.TIMEOUT
        self._timeout = settings.TIMEOUT
        self._decay = settings.DECAY

    def sleep(self):
        logger.info(f"Retrying in {self._timeout} seconds")
        time.sleep(self._timeout)
        self._timeout = min(self._max_timeout, self._timeout * self._decay)

    def reset(self):
        self._timeout = self._org_timeout
