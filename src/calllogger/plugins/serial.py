# Standard library
from typing import NoReturn, Union
from pathlib import PosixPath
import logging
import abc
import sys

# Third party
import serial
from sentry_sdk import push_scope, capture_exception, Scope

# Local
from calllogger.record import CallDataRecord
from calllogger.plugins.base import BasePlugin
from calllogger import settings, metrics

logger = logging.getLogger(__name__)


class ParseError(RuntimeError):
    pass


class ValidationError(ValueError):
    pass


class EmptyLine(ValidationError):
    pass


# noinspection PyMethodMayBeStatic
class SerialPlugin(BasePlugin):
    """
    This is an extended base plugin with serial interface support.

    .. note:: This class is not ment to be called directly, but subclassed by a Plugin.
    """

    #: The serial baudrate to use.
    baudrate: int = 9600
    #: The serial port to comunicate with.
    port: PosixPath = PosixPath("/dev/ttyUSB0")

    def __init__(self):
        super(SerialPlugin, self).__init__()
        self.sserver = serial.Serial()

        # Check if serial port exists
        if not self.port.exists():
            print(f"The target serial port '{self.port}' can't be found.")
            if settings.dockerized:
                print("Please add the following to your docker command.")
                print(f"--device={self.port}:{self.port}")
            sys.exit(0)

    def __open(self):
        """Open a connection to the serial interface, returning True if successful else False."""
        try:
            self.sserver.baudrate = self.baudrate
            self.sserver.port = str(self.port)
            self.sserver.open()
        except Exception:
            logger.debug("Failed to connect to serial interface")
            metrics.serial_conn_error_counter.inc()
            self.timeout.sleep()
            self.sserver.close()
            raise

    def __read(self) -> bytes:
        """Read in a line from the serial interface."""
        try:
            return self.sserver.readline()
        except Exception:
            logger.debug("Failed to read from serial interface")
            metrics.serial_read_error_counter.inc()
            self.timeout.sleep()
            self.sserver.close()
            raise

    def __decode(self, raw: bytes) -> str:
        try:
            return self.decode(raw)
        except Exception:
            logger.debug("Failed to decode serial line: %r", raw)
            metrics.failed_decode_counter.inc()
            raise

    def decode(self, raw: bytes) -> str:
        """
        Decode the serial line into unicode using the ASCII encoding.
        Overide this method to handel the decoding of the serial data with a different encoding.

        :param raw: The raw data line from the serial interface as type ``bytes``.
        :returns: The raw data line decoded into type ``str``.
        """
        return raw.decode("ASCII")

    def __validate(self, decoded_line: str) -> Union[str, bool]:
        try:
            # Validate can return False for failed validation or an
            # empty string if no data is left after stripping whitespace
            if validated_line := self.validate(decoded_line):
                return validated_line
            elif validated_line == "":
                raise EmptyLine("Serial line is empty")
            else:
                raise ValidationError("Validation failed")
        except EmptyLine:
            logger.debug("Serial line is empty, ignoring")
            metrics.empty_line_counter.inc()
            raise
        except Exception:
            logger.debug("Serial line failed validation: %s", decoded_line)
            metrics.failed_validation_counter.inc()
            raise

    def validate(self, decoded_line: str) -> Union[str, bool]:
        """
        Strip out any whitespaces from the serial data and return.
        Overide this method to do custom validation on the serial data.

        You can use this method to check if serial line is of the correct length.
        Or if it contains the right kind of data for example.

        :param str decoded_line: The decoded data line from the serial interface.
        :returns: The validated serial line, or False if validation failed.
        """
        return decoded_line.strip()

    def __parse(self, validated_line: str) -> CallDataRecord:
        try:
            if record := self.parse(validated_line):
                return record
            else:
                raise ParseError("Invalid return type")
        except Exception:
            logger.debug("Failed to parse serial line: %s", validated_line)
            metrics.failed_parse_counter.inc()
            raise

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
                    self.monitor_interface(scope)
                except Exception as err:
                    scope.set_context("Serial Interface", {
                        "baudrate": self.baudrate,
                        "port": str(self.port),
                    })
                    capture_exception(err, scope=scope)
                else:
                    self.timeout.reset()

    def monitor_interface(self, scope: Scope):
        # Ensure that the serial connection is open
        if not self.sserver.is_open:
            self.__open()

        # Read the raw serial line
        raw_line = self.__read()
        scope.set_extra("raw_line", repr(raw_line))

        # Decode the serial line
        decoded_line = self.__decode(raw_line)
        scope.set_extra("decoded_line", decoded_line)

        # Validate the decoded serial line
        validated_line = self.__validate(decoded_line)
        scope.set_extra("validated_line", validated_line)

        # Parse the serial line and push to the cloud
        record = self.__parse(validated_line)
        self.push(record)
