# Standard library
import random
import time

# Local
from typing import NoReturn

from calllogger.plugins import BasePlugin
from calllogger.record import CallDataRecord

# Set of predefined numbers to
# create mock calls from
callset = [
    "0857539075",  # Michael Forde
    "0873575643",  # Tom Baker
    "0853436640",  # Jerry Cremin
    "0277665604",  # Louie Walsh
    "0107974846",  # Tim Barra
    "0213268621",  # Mike Twomey
    "0850549045",  # Philip Murray
    "0877644458",  # Maura Jenkins
    "0667126317", "0667124800", "0667199999", "0214274845",
    "0214365241", "016643658", "0212355545", "018302044",
]


class Mockmonitor(BasePlugin):
    """Generate random call records continuously."""

    sleep: float = 1.5  # Time in seconds to delay, 0 will skip incoming and push at full speed.
    direction: float = 0.5  # Determine preferred call direction, Outgoing is 0 and Received is 1.
    lines: int = 3  # Number of phone lines.
    exts: int = 20  # Number of extensions.

    # noinspection PyMethodMayBeStatic
    def rand_number(self) -> str:
        return callset[random.randrange(len(callset))]

    def rand_line(self) -> int:
        return random.randrange(1, self.lines+1)

    def rand_ext(self) -> int:
        return random.randrange(100, 100+self.exts)

    def entrypoint(self) -> NoReturn:
        while self.is_running:
            # Generate random call data
            number = self.rand_number()
            line = self.rand_line()

            # Deside if call is Outgoing or Received
            if random.random() > self.direction:
                self.outgoing(number, line)
            else:
                self.received(number, line)

            # Sleep between records if requested
            if self.sleep:
                time.sleep(self.sleep)

    def outgoing(self, number, line):
        record = CallDataRecord(call_type=2)
        record.number = number
        record.line = line
        record.ext = self.rand_ext()
        record.ring = random.randrange(1, 20)
        record.duration = 0 if random.randrange(5) == 0 else random.randrange(0, 10000)
        self.push(record)

    def received(self, number, line):
        duration = 0 if random.randrange(5) == 0 else random.randrange(0, 10000)
        ring = random.randrange(1, 10)
        ext = self.rand_ext()

        # If we are sleeping before the next record
        # We want to add the Incoming records
        if self.sleep:
            # Use the ring time to select the delay and number
            # of hops before jumping to next extention
            for hop in range(int(ring / 4)):
                ext = random.randrange(100, 125)

                record = CallDataRecord(call_type=0)
                record.number = number,
                record.line = line,
                record.ext = ext
                self.push(record)

                time.sleep(hop)

        # Send received record
        record = CallDataRecord(call_type=1)
        record.number = number
        record.line = line
        record.ext = ext
        record.ring = ring
        record.duration = duration
        self.push(record)
