# Standard library
from typing import Dict, Type, NoReturn
import threading
import logging
import queue
import time
import abc

# Third party
import serial

# Package imports
from quartx_call_logger import api, settings
from quartx_call_logger.record import Record

logger = logging.getLogger(__name__)

__all__ = ["Plugin", "SerialPlugin"]


class Plugin(metaclass=abc.ABCMeta):
    """
    This is the Base Plugin class for all phone system plugins.

    .. note:: This class is not ment to be called directly, but subclassed by a Plugin.
    """

    # Call logger settings
    settings = settings

    # noinspection PyMethodOverriding, PyMethodParameters
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        logger.debug(f"Registering plugin: {cls.__name__} {cls}")

        # Register plugin
        if cls.__name__.lower() in registered_plugins:
            raise ValueError(f"Plugin with name '{cls.__name__.lower()}' already exists")
        else:
            registered_plugins[cls.__name__.lower()] = cls

    def __init__(self):
        # Setup buffer queue
        self._queue = queue.Queue(settings.QUEUE_SIZE)

        # Running Flag, Indecates that the API is still working
        self._running = threading.Event()
        self._running.set()

        # Start the API thread to monitor for call records and send them to server
        self._api_thread = api.API(self._queue, self._running)
        self._api_thread.start()

        #: Create plugin specific logger with the name of the Sub classed plugin
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        #: Public settings
        self.settings = settings

    def start(self) -> NoReturn:
        try:
            self.run()
        except KeyboardInterrupt:
            self.logger.debug("Keyboard Interrupt accepted.")
        finally:
            self._running.clear()

    @property
    def running(self) -> bool:
        """Flag to indicate that everything is working and ready to keep monitoring."""
        return self._running.is_set()

    def push(self, record: Record) -> NoReturn:
        """Send a call log record to the call monitoring API."""
        cleaned = record.clean()
        self._queue.put(cleaned)

    @abc.abstractmethod
    def run(self) -> NoReturn:  # pragma: no cover
        """Main entry point for plugin. Must be overridden"""
        pass


# All register plugin's
registered_plugins: Dict[str, Type[Plugin]] = {}


class SerialPlugin(Plugin):
    """
    This is an extended plugin with serial interface support.

    .. note:: This class is not ment to be called directly, but subclassed by a Plugin.

    :param port: The port/path to the serial interface.
    :param rate: The serial baud rate to use.
    """
    def __init__(self, port: str, rate: int):
        super(SerialPlugin, self).__init__()

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
        except serial.SerialException:
            # Sleep for a while before reattempting connection
            self.logger.error("Failed to open serial connection")
            self.logger.info(f"Retrying in {settings.TIMEOUT} seconds")
            time.sleep(settings.TIMEOUT)
            return False
        else:
            self.logger.debug(f"Conection made to serial interface: {self.sserver.port}")
            return True

    def __read(self) -> str:
        """Read in a line from the serial interface."""
        try:
            line = self.sserver.readline()
        except serial.SerialException:
            self.sserver.close()
            self.logger.error("Failed to read serial line")
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
                    self.logger.error(f"Failed to parse serial line", extra={"data": serial_line})
                    self.logger.debug(e)
                else:
                    # Push record to the cloud
                    if record:
                        self.push(record)


def get_plugin(plugin_name: str) -> Type[Plugin]:
    """Return pluging matching the given name."""
    try:
        return registered_plugins[plugin_name.lower()]
    except KeyError:
        raise KeyError(f"plugin not found: {plugin_name.lower()}")
