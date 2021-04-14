# Standard library
from typing import NoReturn, Union
import abc

# Third party
import serial
from sentry_sdk import push_scope, capture_exception, Scope

# Local
from calllogger.record import CallDataRecord
from calllogger.plugins.base import BasePlugin


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

    def __open(self):
        """Open a connection to the serial interface, returning True if successful else False."""
        try:
            self.sserver.baudrate = self.baudrate
            self.sserver.port = self.port
            self.sserver.open()
        except Exception:
            self.timeout.sleep()
            self.sserver.close()
            raise

    def __read(self) -> bytes:
        """Read in a line from the serial interface."""
        try:
            return self.sserver.readline()
        except Exception:
            self.timeout.sleep()
            self.sserver.close()
            raise

    def decode(self, raw: bytes) -> str:
        """
        Decode the serial line into unicode using the ASCII encoding.
        Overide this method to handel the decoding of the serial data with a different encoding.

        :param raw: The raw data line from the serial interface as type ``bytes``.
        :returns: The raw data line decoded into type ``str``.
        """
        return raw.decode("ASCII")

    def validate(self, decoded_line: str) -> Union[str, bool]:
        """
        Overide this method if you wish to validate the serial line.

        You can use this method to check if serial line is the
        correct length or that it's not empty after running strip().

        :param str decoded_line: The decoded data line from the serial interface.
        :returns: The validated serial line, or False if validation failed.
        """
        return decoded_line

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
                try:
                    # Ensure that the serial connection is open
                    if not self.sserver.is_open:
                        self.__open()

                    self.monitor_interface(scope)
                except Exception as err:
                    scope.set_context("Serial Interface", {
                        "baudrate": self.baudrate,
                        "port": self.port,
                    })
                    capture_exception(err, scope=scope)
                else:
                    self.timeout.reset()

    def monitor_interface(self, scope: Scope):
        # Read the raw serial line
        raw_line = self.__read()
        scope.set_extra("raw_line", repr(raw_line))

        # Decode the serial line
        decoded_line = self.decode(raw_line)
        scope.set_extra("decoded_line", decoded_line)

        # Validate the decoded serial line
        if validated_line := self.validate(decoded_line):
            scope.set_extra("validated_line", validated_line)

            # Parse the serial line and push to the cloud
            if record := self.parse(validated_line):
                self.push(record)
            else:
                self.logger.error("Non valid data returned from parser")
        else:
            self.logger.error("Serial line is invalid")
