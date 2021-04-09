# Standard library
from typing import NoReturn, Union
import logging
import abc

# Third party
import serial
from sentry_sdk import push_scope, capture_exception, Scope

# Local
from calllogger.record import CallDataRecord
from calllogger.plugins.base import BasePlugin

logger = logging.getLogger(__name__)
installed_plugins = {}


# noinspection PyMethodMayBeStatic
class SerialPlugin(BasePlugin):
    """
    This is an extended base plugin with serial interface support.

    .. note:: This class is not ment to be called directly, but subclassed by a Plugin.
    """

    #: The serial baudrate to use.
    baudrate: int = 9600
    #: The serial port to comunicate with.
    port: str = "/dev/ttyUSB0"

    def __init__(self):
        super(SerialPlugin, self).__init__()
        self.sserver = serial.Serial()

    def __open(self) -> bool:
        """Open a connection to the serial interface, returning True if successful else False."""
        try:
            # We set the port & rate here to allow them to be changed on the fly
            self.sserver.baudrate = self.baudrate
            self.sserver.port = self.port
            self.sserver.open()
        except serial.SerialException:
            self.logger.error("Failed to open serial connection", extra={
                "baudrate": self.sserver.baudrate,
                "port": self.sserver.port,
            })
            return False
        else:
            self.logger.debug(f"Conection made to serial interface: {self.sserver.port},{self.sserver.baudrate}")
            return True

    def __read(self, scope: Scope) -> Union[bytes, None]:
        """Read in a line from the serial interface."""
        try:
            return self.sserver.readline()
        except serial.SerialException as err:
            # Refresh the serial interface by closing the serial connection
            capture_exception(err, scope=scope)
            self.sserver.close()
            return None

    def __decode(self, scope: Scope, raw: bytes) -> str:
        try:
            return self.decode(raw)
        except Exception as err:
            capture_exception(err, scope=scope)

    def decode(self, raw: bytes) -> str:  # pragma: no cover
        """
        Decode the serial line into unicode using the ASCII encoding.
        Overide this method to handel the decoding of the serial data with a different encoding.

        :param raw: The raw data line from the serial interface as type ``bytes``.
        :returns: The raw data line decoded into type ``str``.
        """
        return raw.decode("ASCII")

    def __validate(self, scope: Scope, decoded_line: str) -> Union[str, bool]:
        try:
            validated = self.validate(decoded_line)
        except Exception as err:
            capture_exception(err, scope=scope)
            return False
        else:
            if validated is False:
                self.logger.error("Serial line is invalid")
            return validated

    def validate(self, decoded_line: str) -> Union[str, bool]:  # pragma: no cover
        """
        Overide this method if you wish to validate the serial line.

        You can use this method to check if serial line is the
        correct length or that it's not empty after running strip().

        :param str decoded_line: The raw data line from the serial interface.
        :returns: The validated serial line, or False if validation failed.
        """
        return decoded_line

    def __parse(self, scope: Scope, validated_line: str) -> CallDataRecord:
        try:
            # Parse the line wtih the selected parser
            return self.parse(validated_line)
        except Exception as err:
            capture_exception(err, scope=scope)

    @abc.abstractmethod
    def parse(self, validated_line: str) -> CallDataRecord:  # pragma: no cover
        """
        Overide this method to handel parsing of serial data.

        :param str validated_line: The decoded serial line.
        :returns: A :class:`calllogger.CallDataRecord` object.
        """
        pass

    def entrypoint(self) -> NoReturn:
        """
        Start the call monitoring loop. Reads a call record from the
        serial interface, parse and push to QuartX Call Monitoring.
        """
        while self.is_running:
            with push_scope() as scope:
                # TODO: Replace scope.set_extra for serial with plugin settings context
                scope.set_extra("baudrate", self.baudrate)
                scope.set_extra("port", self.port)

                # Open serial port connection
                if not (self.sserver.is_open or self.__open()):
                    # Sleep for a while before reattempting connection
                    self.timeout.sleep()
                    continue
                else:
                    self.timeout.reset()

                # Read the raw serial line
                raw_line = self.__read(scope)
                if raw_line is None:
                    continue

                # Decode the serial line
                scope.set_extra("raw_line", raw_line)
                decoded_line = self.__decode(scope, raw_line)
                if decoded_line is None:
                    continue

                # Validate the decoded serial line
                scope.set_extra("decoded_line", decoded_line)
                validated_line = self.__validate(scope, decoded_line)
                if validated_line is False:
                    continue

                # Parse the serial line and push to the cloud
                scope.set_extra("validated_line", validated_line)
                if record := self.__parse(scope, validated_line):
                    self.push(record)
