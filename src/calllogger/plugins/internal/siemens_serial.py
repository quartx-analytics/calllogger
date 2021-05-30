__all__ = ["SiemensHipathSerial"]

# Standard library
from datetime import timezone
from typing import Union

# Package imports
from calllogger.plugins import SerialPlugin
from calllogger.record import CallDataRecord

# Set of Control Characters the we don't need nor want
# https://donsnotes.com/tech/charsets/ascii.html
control_char_map = dict.fromkeys(range(32))


# noinspection PyMethodMayBeStatic
class SiemensHipathSerial(SerialPlugin):
    """Data object for call logs."""

    def decode(self, raw: bytes) -> str:
        decoded_line = raw.decode("ASCII")
        return decoded_line.translate(control_char_map)

    def validate(self, decoded_line: str) -> Union[str, bool]:
        """Validate that the line contains data and is at least the right length."""
        line = decoded_line.rstrip()  # Gets rid of end of line crap
        return False if len(line) < 76 else line

    def parse(self, validated_line: str) -> CallDataRecord:
        """Parse call logs received from the a Siemans Hipath serial interface."""
        # Parse the received record
        call_type = validated_line[74:76].strip()
        record = CallDataRecord(int(call_type))

        # Add date as UTC
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        record.date_str(validated_line[:16], fmt="%d.%m.%y%X", tz=timezone.utc)

        # Example serial output
        # |--------------|--|-----|----|-------|------------------------|----------|-|
        # 11.04.1900:35:48  1   10400:0100:00:070876153281                           1
        record.line = validated_line[16:19]
        record.ext = validated_line[19:25]
        record.ring = validated_line[25:30]
        record.duration = validated_line[30:38]
        record.number = validated_line[38:63]

        # Return processed call record
        return record
