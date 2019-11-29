# Standard library
from typing import Dict, Type, NoReturn
import logging
import queue
import time
import abc

# Third party
import serial

# Package imports
from .. import api
from ..record import Record

logger = logging.getLogger(__name__)


class DuplicatePlugin(ValueError):
    pass


class Plugin(metaclass=abc.ABCMeta):
    """
    This is the Base Plugin class for all phone system plugins.

    This class is not ment to be called directly, but subclassed by a Plugin.
    """

    # noinspection PyMethodOverriding, PyMethodParameters
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        logger.debug(f"Registering plugin: {cls.__name__} {cls}")
        if cls.__name__.lower() in registered_plugins:
            raise DuplicatePlugin(f"Plugin with name '{cls.__name__.lower()}' already exists")
        else:
            registered_plugins[cls.__name__.lower()] = cls

    def __init__(self, timeout=10, max_timeout=300, decay=1.5, **settings):
        self.queue = queue.Queue(10_000)
        self._api_thread = api.API(self.queue)
        self._api_thread.start()

        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.timeout: int = timeout
        self.timeout_decay: float = decay
        self.max_timeout: int = max_timeout
        self.base_timeout: int = timeout

    def start(self, **settings):
        # Update the internal settings
        self.__dict__.update(settings)
        self.base_timeout = self.timeout

        try:
            self.run()
        except KeyboardInterrupt:
            self.logger.debug("Keyboard Interrupt accepted.")
        except Exception as err:
            self.logger.debug("unhandled expection: %s", str(err), exc_info=True)
            raise
        finally:
            self._api_thread.running.clear()

    @property
    def running(self) -> bool:
        """Flag to indecate that everything is working and ready to keep monitoring."""
        return self._api_thread.running.is_set()

    def push(self, record: Record) -> NoReturn:
        """Send a call log record to the call monitoring API."""
        self.queue.put(record)

    @abc.abstractmethod
    def run(self) -> NoReturn:  # pragma: no cover
        """Main entry point for plugin. Must be overridden"""
        pass


# All register plugin's
registered_plugins: Dict[str, Type[Plugin]] = {}


class SerialPlugin(Plugin):
    """
    This is an extended plugin with serial interface support.

    This class is not ment to be called directly, but subclassed by a Plugin.

    :param port: The port/path to the serial interface.
    :param rate: The serial baud rate to use.
    """
    def __init__(self, port: str, rate: int, **settings):
        super(SerialPlugin, self).__init__(**settings)

        # Setup serial interface
        self.sserver = ser = serial.Serial()
        ser.baudrate = rate
        ser.port = port

    @abc.abstractmethod
    def decode(self, data: bytes) -> str:  # pragma: no cover
        """
        Overide this method to handel decoding of serial data.

        :param data: The raw data line from the serial interface as type ``bytes``.
        :returns: The decoded into data line as type ``str``.
        """
        pass

    @abc.abstractmethod
    def parse(self, data: str) -> Record:  # pragma: no cover
        """
        Overide this method to handel parsing of serial data.

        :param data: The decoded data line.
        :returns: A :class:`quartx_call_logger.record.Record` object.
        """
        pass

    def __open(self) -> bool:
        """Open a connection to the serial interface, returning True if successful else False."""
        try:
            # Attemp to open serial port
            self.sserver.open()
        except serial.SerialException as e:
            # Sleep for a while before reattempting connection
            self.logger.error(e)
            self.logger.info(f"Retrying in {self.timeout} seconds")
            time.sleep(self.timeout)
            return False
        else:
            self.logger.debug(f"Conection made to serial interface: {self.sserver.port}")
            return True

    def __read(self) -> str:
        """Read in a call line from the serial interface."""
        try:
            line = self.sserver.readline()
        except serial.SerialException as e:
            self.sserver.close()
            self.logger.error(e)
        else:
            # Decode the line into unicode
            return self.decode(line)

    def run(self) -> NoReturn:
        """
        Start the call monitoring loop. Reads a call record from the
        serial interface, parse and push to QuartX Call Monitoring.
        """
        while self.running:
            # Open serial port connection
            if not (self.sserver.is_open or self.__open()):
                continue

            # Read the raw serial input and parse
            serial_line = self.__read()
            if serial_line:
                try:
                    # Parse the line wtih the selected parser
                    record = self.parse(serial_line)
                except Exception as e:
                    self.logger.error(f"Failed to process line: {serial_line.strip()}")
                    self.logger.exception(e)
                else:
                    # Push record to the cloud
                    if record:
                        self.push(record)


def get_plugin(plugin_name: str) -> Type[Plugin]:
    """Return pluging matching the given name."""
    try:
        # Load required plugin
        return registered_plugins[plugin_name.lower()]
    except KeyError:
        raise KeyError(f"plugin not found: {plugin_name.lower()}")
