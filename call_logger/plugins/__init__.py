# Standard library
from typing import Dict, Type, NoReturn, Iterator
from datetime import datetime, timezone
from collections.abc import MutableMapping
import time
import abc

# Third party
import phonenumbers
import serial

# Package imports
from .. import config, logger

# Answered field
NOT_ANSWERED = 0
ANSWERED = 1
VOICEMAIL = 2

# Calltype field
INCOMING = 0
RECEIVED = 1
OUTGOING = 2


class Call(MutableMapping):
    """
    Common required fields.
    number, line, ext

    Fields required by Received & Outgoing call logs.
    ring, duration

    Optinal fields for Received & Outgoing call logs.
    answered, date
    """

    def __setitem__(self, k, v) -> None:
        self.data[k] = self._parse_phone_num(v) if k == "number" else v

    def __delitem__(self, k) -> None:
        del self.data[k]

    def __getitem__(self, k):
        return self.data[k]

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator:
        return iter(self.data)

    def __init__(self, calltype: int, **kwargs):
        self.call_type = calltype
        if calltype != INCOMING:
            if "call_type" not in kwargs:
                kwargs["call_type"] = calltype

            if "date" not in kwargs:
                kwargs["date"] = datetime.now(timezone.utc).isoformat()

        self.data = {}
        # Update the dict class
        self.update(kwargs)

    def __repr__(self):
        data = ", ".join([f"{name}={repr(value)}" for name, value in self.items()])
        return f"Call({self.call_type}, {data})"

    def __str__(self):
        data = ", ".join([f"{name}={repr(value)}" for name, value in self.items()])
        str_call_type = ["incoming", "received", "outgoing"][self.call_type]
        return f"{str_call_type.title()}({data})"

    @staticmethod
    def _parse_phone_num(num) -> str:
        """
        Parse phone number to add international code if required.
        Returning the full E164 international number.
        """
        region_code = config["settings"].get("region_code", "IE")
        num_obj = phonenumbers.parse(num, region_code)

        # Return the number as the full E164 international phone number
        return phonenumbers.format_number(num_obj, phonenumbers.PhoneNumberFormat.E164)

    def copy(self):
        return Call(self.call_type, **self.data)


class BasePlugin(object):
    """
    This is the Base class for all phone system parsers.
    It's not that useful now but will be when we support more than 1 phone system.
    """

    # The name of the plugin (Required)
    name: str = None

    def __init__(self, *args, **kwargs):
        # This method is just for signature purposes
        pass

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


class SerialMonitor(metaclass=abc.ABCMeta):
    """
    This monitor is used for monitoring the serial interface for call logs.
    Using the newline character as the delimiter.
    """
    def __init__(self, port: str, rate: int, **kwargs):
        super(SerialMonitor, self).__init__(**kwargs)
        self.timeout = config["settings"].getint("timeout")

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


# All register system plugin's
systems: Dict[str, Type[BasePlugin]] = {}
