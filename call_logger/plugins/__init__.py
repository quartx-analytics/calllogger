# Standard library
from typing import Dict, Type, NoReturn
import logging
import time
import abc

# Third party
import serial

# Package imports
from .. import api
from ..record import Record

logger = logging.getLogger(__name__)


class Plugin(metaclass=abc.ABCMeta):
    """This is the Base class for all phone system parsers."""

    # noinspection PyMethodOverriding, PyMethodParameters
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        logger.debug(f"Registering plugin: {cls.__name__} {cls}")
        if cls.__name__.lower() in plugins:
            raise RuntimeError(f"Plugin with name '{cls.__name__.lower()}' already exists")
        else:
            plugins[cls.__name__.lower()] = cls

    def __init__(self, timeout: int, max_timeout: int, decay: float, **settings):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._api_thread = api.API()
        self._api_thread.start()

        # TODO: Find a better way to handle timeout decay
        self.max_timeout = max_timeout
        self.timeout_decay = decay
        self.timeout = timeout

    @property
    def running(self) -> bool:
        """Flag to indecate that the api thread is still running."""
        return self._api_thread.running

    @running.setter
    def running(self, value: bool) -> NoReturn:
        self._api_thread.running = value

    def push(self, record: Record) -> NoReturn:
        """Send a call log to the api."""
        self._api_thread.log(record)

    @abc.abstractmethod
    def run(self) -> NoReturn:
        """Main entry point for plugin. Must be overridden"""
        pass


class SerialPlugin(Plugin):
    """
    This is an extended plugin with serial interface support.

    :param str port: The port/path to the serial interface.
    :param int rate: The serial baud rate to use.
    """
    def __init__(self, port: str, rate: int, **settings):
        super(SerialPlugin, self).__init__(**settings)

        # Setup serial interface
        self.sserver = ser = serial.Serial()
        ser.baudrate = rate
        ser.port = port

    @abc.abstractmethod
    def decode(self, line: bytes) -> str:
        """Overide to handel decoding of serial data."""
        pass

    @abc.abstractmethod
    def parse(self, line: str) -> Record:
        """Overide to handel parsing of serial data."""
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
            self.timeout = min(self.max_timeout, self.timeout * self.timeout_decay)
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
        serial interface, parse and push to glaonna monitoring.
        """
        while self.running:
            try:
                # Open serial port connection
                if not (self.sserver.is_open or self.__open()):
                    continue

                # Read the raw serial input and parse
                serial_line = self.__read()
                if serial_line:
                    self.logger.debug(f"Processing line: {serial_line.strip()}")

                    try:
                        # Parse the line wtih the selected parser
                        record = self.parse(serial_line)
                    except Exception as e:
                        self.logger.error(f"Failed to process line: {serial_line}")
                        self.logger.exception(e)
                    else:
                        # Push record to the cloud
                        self.push(record)

            except KeyboardInterrupt:
                # noinspection PyAttributeOutsideInit
                self.running = False


def get_plugin(plugin_name: str) -> Type[Plugin]:
    """Return pluging matching the given name."""
    try:
        # Load required plugin
        return plugins[plugin_name.lower()]
    except KeyError:
        raise KeyError(f"plugin not found: {plugin_name.lower()}")


# All register plugin's
plugins: Dict[str, Type[Plugin]] = {}
