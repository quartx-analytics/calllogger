__all__ = ["SiemensHipathSerial"]

# Standard library
from datetime import timezone
from typing import Union

# Package imports
from calllogger.plugins import SerialPlugin
from calllogger.record import CallDataRecord


# noinspection PyMethodMayBeStatic
class SiemensHipathSerial(SerialPlugin):
    """Data object for call logs."""

    def validate(self, decoded_line: str) -> Union[str, bool]:
        """Validate that the line contains data and is at least the right length."""
        # TODO: Some lines have garbled data but still contain the data we need. We need to filter out the crap.
        line = decoded_line.strip()
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
