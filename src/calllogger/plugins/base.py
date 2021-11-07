# Standard library
from typing import NoReturn
from queue import SimpleQueue
import logging
import abc

# Local
from calllogger import stopped, settings, conf
from calllogger.misc import ThreadExceptionManager
from calllogger.record import CallDataRecord
from calllogger.utils import Timeout

logger = logging.getLogger(__name__)
record_logger = logging.getLogger("calllogger.record")
installed_plugins = {}


class PluginSettings(abc.ABCMeta):
    """Metaclass to intercept the init call and apply the plugin settings."""

    def __call__(cls, **kwargs):
        inst = super().__call__()
        conf.merge_settings(inst, prefix="plugin_", **kwargs)
        return inst


class BasePlugin(ThreadExceptionManager, metaclass=PluginSettings):
    """
    This is the Base Plugin class for all phone system plugins.

    .. note:: This class is not ment to be called directly, but subclassed by a Plugin.
    """
    id = None
    _queue: SimpleQueue

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        super(BasePlugin, self).__init__(name=f"Thread-{self.__class__.__name__}")
        self.logger.info("Initializing plugin: %s", self.__class__.__name__)

        #: Timeout control, Used to control the timeout decay when repeatedly called.
        self.timeout = Timeout(settings, stopped)  # pragma: no branch
        self.stopped = stopped

    def push(self, record: CallDataRecord) -> NoReturn:
        """Send a call log record to the call monitoring API."""
        if self._queue.qsize() < settings.queue_size:
            self._queue.put(record)
        else:
            logger.warning(
                f"CDR Queue is full {self._queue.qsize()}",
                extra={"queue_size": self._queue.qsize()},
            )

            # As we are forced to use a simpleQueue it's not as easy to block
            while not self.stopped.wait(0.1):
                # The Queue has space now
                if self._queue.qsize() < settings.queue_size:
                    self._queue.put(record)
                    break

            logger.warning(
                f"CDR Queue is no longer full {self._queue.qsize()}",
                extra={"queue_size": self._queue.qsize()}
            )

        record_logger.debug(record)

    @property
    def is_running(self) -> bool:
        """Flag to indicate that everything is working and ready to keep monitoring."""
        return not self.stopped.is_set()

    @abc.abstractmethod
    def entrypoint(self) -> NoReturn:  # pragma: no cover
        """Main entry point for the plugins. Must be overridden."""
        raise NotImplementedError
