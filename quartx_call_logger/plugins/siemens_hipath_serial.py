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
        # Parse the received record
        call = Record()

        # Parse the CDR data
        call["date"] = datetime.strptime(data[:16], "%d.%m.%y%X").astimezone(timezone.utc).isoformat()  # DateTime
        call["line"] = data[16:19].strip()  # Line
        call["ext"] = data[19:25].strip()  # Extension
        call["ring"] = data[25:30].strip()  # ring duration
        call["duration"] = data[30:38].strip()  # call duration
        call["number"] = data[38:63].strip()  # phone number
        call["charges"] = data[63:74].strip()  # call charges
        call["call_type"] = data[74:76].strip()  # call type
        call["acct"] = data[76:87].strip()  # ACCT
        call["msn"] = data[87:88].strip()  # MSN
        call["seizure_code"] = data[88:93].strip()  # seizure code
        call["lcr"] = data[93:95].strip()  # LCR

        # Return processed call record
        return call
