# Standard library
from typing import Dict, Type, NoReturn

import time
import abc

# Third party
import serial

# Package imports
from .. import logger, api


def load_plugins():
    """Import all plugin's so they can be registered."""
    prefix = plugins.__name__ + "."
    for _, modname, _ in pkgutil.iter_modules(plugins.__path__, prefix):
        __import__(modname)


class BasePlugin(metaclass=abc.ABCMeta):
    """
    This is the Base class for all phone system parsers.
    It's not that useful now but will be when we support more than 1 phone system.
    """

    # The name of the plugin (Required)
    name: str = None

    # noinspection PyUnusedLocal
    def __init__(self, **settings):
        self.settings = settings
        self.api_thread = api.API()
        self.api_thread.start()
        # TODO: Exit script if api is not running

    def log(self, record):
        """Send a call log to the api."""
        self.api_thread.log(record)

    @staticmethod
    def time_in_seconds(duration: str) -> int:
        """Convert duration in the format of "00:00:00" to seconds."""
        time_parts = duration.split(":")
        time_parts.reverse()
        duration = 0
        counter = 1

        for part in time_parts:
            duration += int(part) * counter
            counter *= 60

        return duration

    def run(self):
        pass


class SerialMonitor(BasePlugin):
    """
    This monitor is used for monitoring the serial interface for call logs.
    Using the newline character as the delimiter.
    """
    def __init__(self, port: str, rate: int, **settings):
        super(SerialMonitor, self).__init__(**settings)


        # Setup serial interface
        self.sserver = ser = serial.Serial()
        ser.baudrate = rate
        ser.port = port

    @abc.abstractmethod
    def decode(self, line: bytes) -> str:
        pass

    @abc.abstractmethod
    def parse(self, line: str):
        pass

    def __open(self) -> bool:
        """Open a connection to the serial interface, returning True if successful else False."""
        try:
            # Attemp to open serial port
            self.sserver.open()
        except serial.SerialException as e:
            # Sleep for a while before reattempting connection
            logger.error(e)
            logger.info(f"Retrying in {self.timeout} seconds")
            time.sleep(self.timeout)
            return False
        else:
            logger.debug(f"Conection made to serial interface: {self.sserver.port}")
            return True

    def __read(self) -> str:
        """Read in a call line from the serial interface."""
        try:
            line = self.sserver.readline()
        except serial.SerialException as e:
            self.sserver.close()
            logger.error(e)
        else:
            # Decode the line into unicode
            return self.decode(line)

    def start(self) -> NoReturn:
        """
        Start the call monitoring loop. Reads a call record from the
        serial interface and add the record to a call queue for processing.
        """
        while True:
            try:
                # Open serial port connection
                if not (self.sserver.is_open or self.__open()):
                    continue

                # Read the raw serial input and parse
                serial_line = self.__read()
                if serial_line:
                    logger.debug(f"Processing line: {serial_line.strip()}")

                    try:
                        # Parse the line wtih the selected parser
                        self.parse(serial_line)
                    except Exception as e:
                        logger.error(f"Failed to process line: {serial_line}")
                        logger.exception(e)

            except KeyboardInterrupt:
                break


def register(cls: Type[BasePlugin]) -> Type[BasePlugin]:
    """
    Decorator to register parser plugins.
    All parsers must call the decorator before they can be used.
    """
    if cls.name is None:
        raise RuntimeError(f"plugin '{cls}' is missing required name attribute")

    logger.debug(f"Registering plugin: {cls.name} {cls}")
    systems[cls.name.lower()] = cls
    return cls


def get_plugin(plugin_name: str) -> Type[BasePlugin]:
    """Return pluging matching the given name."""
    try:
        # Load required plugin
        return systems[plugin_name.lower()]
    except KeyError:
        raise KeyError(f"plugin not found: {plugin_name}")


# All register system plugin's
systems: Dict[str, Type[BasePlugin]] = {}
