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
        self._api_thread = api.API()
        self._api_thread.start()

        #: The logger object associated with this plugin
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        #: The timeout setting in seconds
        self.timeout: int = timeout
        #: The timeout decay, the timeout will get longer after each failed connection
        self.timeout_decay: float = decay
        #: The max timeout in seconds, the timeout will not decay past this point
        self.max_timeout: int = max_timeout
        #: The base timeout setting without decay applied
        self.base_timeout: int = timeout

    def start(self):
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
        """Send a call log to the api."""
        self._api_thread.log(record)

    @abc.abstractmethod
    def run(self) -> NoReturn:
        """Main entry point for plugin. Must be overridden"""
        pass


# All register plugin's
plugins: Dict[str, Type[Plugin]] = {}


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
                    if record:
                        self.push(record)


def get_plugin(plugin_name: str) -> Type[Plugin]:
    """Return pluging matching the given name."""
    try:
        # Load required plugin
        return plugins[plugin_name.lower()]
    except KeyError:
        raise KeyError(f"plugin not found: {plugin_name.lower()}")
