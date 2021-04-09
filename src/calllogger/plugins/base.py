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
        self.timeout = Timeout(settings, self._running)

    def run(self):
        try:
            self.entrypoint()
        except Exception as err:
            capture_exception(err)
            self._running.clear()
            # TODO: See whats the better option to do here, quit or try again
            raise

    def log(self, msg: str, *args, lvl: int = logging.INFO, **kwargs) -> NoReturn:
        """
        Send log message to console/server.

        :param msg: The log message.
        :param lvl: The logging level, default to INFO.
        """
        self.logger.log(lvl, msg, *args, **kwargs)

    def push(self, record: CallDataRecord) -> NoReturn:
        """Send a call log record to the call monitoring API."""
        logger.debug(record.data)
        self._queue.put(record.data)

    @property
    def is_running(self) -> bool:
        """Flag to indicate that everything is working and ready to keep monitoring."""
        return self._running.is_set()

    @abc.abstractmethod
    def entrypoint(self) -> NoReturn:  # pragma: no cover
        """Main entry point for the plugins. Must be overridden."""
        pass
