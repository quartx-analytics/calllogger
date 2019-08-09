# Standard library
from datetime import datetime, timezone

# Package imports
from . import SerialPlugin, Record


class SiemensHipathSerial(SerialPlugin):
    """Data object for call logs."""

    def decode(self, data: bytes) -> str:
        return data.decode("ASCII")

    def parse(self, data: str):
        """
        Parse call logs received from the a Siemans Hipath serial interface.

        # Example incoming:
        22.02.1923:11:41 3 048 0248873711 0 4416 -> [date, line, ext, incoming_call, call_type, ddi]
        Call(number='0248873711', ext=48, line=3)

        # Example received
        22.02.1923:11:43 3 04800:4100:10:030248873711 1 4416 -> [date, line, call_data, call_type. ddi]
        Call(date="2019-03-01T21:35:45Z", line=3, ext=48, number='0248873711',
             ring=41, duration=603, answered=1, call_type=1)

        # Example outgoing
        22.02.1922:55:27 3 05800:0700:00:000922735086 2 -> [date, line, call_data, call_type]
        Call(date="2019-03-01T21:35:45Z", line=3, ext=58, number="0922735086",
             ring=7, duration=0, answered=0, call_type=2)
        """
        # Parse the CDR
        raw_date = data[:16]
        line = data[16:19].strip()
        ext = data[22:25].strip()
        ring = data[25:30].strip()
        duration = data[30:38].strip()
        number = data[38:53].strip()
        call_type = int(data[74:77].strip())

        # Parse the received record
        call = Record(call_type, line=int(line) if line else 0)

        # Common
        call["number"] = number if number else "000000000"
        call["ext"] = int(ext) if ext else 0

        # Received & Outgoing calls share common data points
        if call.call_type == Record.RECEIVED or call.call_type == Record.OUTGOING:
            call["date"] = datetime.strptime(raw_date, "%d.%m.%y%X").astimezone(timezone.utc).isoformat()
            call["duration"] = duration
            call["ring"] = ring

        elif not call.call_type == Record.INCOMING:
            self.logger.error(f"unexpected call type: {call_type}")
            self.logger.error(data)

        # Return processed call record
        return call
