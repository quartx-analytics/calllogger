# Standard library
from datetime import datetime, timezone

# Package imports
from .. import logger, config, plugins


@plugins.register
class SiemensHPS(plugins.SerialMonitor, plugins.BasePlugin):
    """Data object for call logs."""
    name = "SiemensHipathSerial"

    def __init__(self, queue_manager, **kwargs):
        self.queue_manager = queue_manager
        settings = config[self.name]
        self.voicemail_ext = settings.getintlist("voicemail_ext")
        rate = settings.getint("rate")
        port = settings["port"]

        # Start the serial monitor and scan for call logs
        super(SiemensHPS, self).__init__(port, rate, **kwargs)
        self.start()

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
        if call_type == plugins.BUSY:
            call_type = 2
            busy = True
        else:
            busy = False

        # Parse the received record
        call = plugins.Call(call_type, line=int(line) if line else 0)

        # Common
        number = number if number else "000000000"
        ext = int(ext) if ext else 0

        # Incoming
        if call.call_type == plugins.INCOMING:
            call["ext"] = int(ext) if ext else 0
            call["number"] = number

        # Received & Outgoing calls share common data points
        elif call.call_type == plugins.RECEIVED or call.call_type == plugins.OUTGOING:
            call["date"] = datetime.strptime(raw_date, "%d.%m.%y%X").astimezone().astimezone(timezone.utc).isoformat()
            call["number"] = number
            call["ext"] = ext = int(ext) if ext else 0
            call["ring"] = self.time_in_seconds(ring) if ring else 0
            call["duration"] = duration = self.time_in_seconds(duration) if duration else 0
            call["answered"] = plugins.BUSY if busy else self.check_if_answered(duration, ext)

        else:
            logger.error(f"unexpected call type: {call_type}")
            logger.error(line, exc_info=True)
            return None

        # Queue the call to be
        # sent to the frontend
        self.queue_manager.put(call)
        logger.info(call)

    def check_if_answered(self, duration: int, ext: int) -> int:
        """Check if call went to voicemail or if the call was answered or not."""
        if duration and ext in self.voicemail_ext:
            return plugins.VOICEMAIL
        elif duration:
            return plugins.ANSWERED
        else:
            return plugins.NOT_ANSWERED
