# Standard library
from datetime import datetime, timezone

# Package imports
from .. import plugins
from ..record import Record


class SiemensHipathSerial(plugins.SerialPlugin):
    """Data object for call logs."""

    def decode(self, line: bytes) -> str:
        return line.decode("ASCII")

    def parse(self, output: str):
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
        raw_date = output[:16]
        line = output[16:19].strip()
        ext = output[22:25].strip()
        ring = output[25:30].strip()
        duration = output[30:38].strip()
        number = output[38:53].strip()
        call_type = int(output[74:77].strip())

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
            self.logger.error(output)

        # Return processed call record
        return call
