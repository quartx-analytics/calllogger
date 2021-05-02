# Standard library
from threading import Event, Thread
from typing import NoReturn
from queue import Queue
import logging
import abc

# Third party
from sentry_sdk import capture_exception

# Local
from calllogger.record import CallDataRecord
from calllogger.utils import Timeout
from calllogger.conf import settings, merge_settings

logger = logging.getLogger(__name__)
installed_plugins = {}


class PluginSettings(abc.ABCMeta):
    """Metaclass to intercept the init call and apply the plugin settings."""

    def __call__(cls, **kwargs):
        inst = super().__call__()
        merge_settings(cls, inst.__dict__, prefix="plugin", **kwargs)
        return inst


class BasePlugin(Thread, metaclass=PluginSettings):
    """
    This is the Base Plugin class for all phone system plugins.

    .. note:: This class is not ment to be called directly, but subclassed by a Plugin.
    """

    _queue: Queue
    _running: Event

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        super(BasePlugin, self).__init__(name=f"Thread-{self.__class__.__name__}")

        #: Timeout control, Used to control the timeout decay when repeatedly called.
        self.timeout = Timeout(settings, lambda: self._running.is_set())  # pragma: no branch

    def run(self) -> bool:
        try:
            self.entrypoint()
        except Exception as err:
            capture_exception(err)
            self._running.clear()
            return False
        else:
            return True

    def push(self, record: CallDataRecord) -> NoReturn:
        """Send a call log record to the call monitoring API."""
        raw_data = record.__dict__
        self._queue.put(raw_data)
        self.logger.debug(raw_data)

    @property
    def is_running(self) -> bool:
        """Flag to indicate that everything is working and ready to keep monitoring."""
        return self._running.is_set()

    @abc.abstractmethod
    def entrypoint(self) -> NoReturn:  # pragma: no cover
        """Main entry point for the plugins. Must be overridden."""
        pass