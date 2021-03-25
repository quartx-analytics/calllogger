# Standard library
import random
import time

# Local
from typing import NoReturn

from calllogger.plugins import BasePlugin
from calllogger.record import CallDataRecord as Record

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


class MockCalls(BasePlugin):
    """Generate random call records continuously."""

    #: Time in seconds to delay, 0 will skip incoming and push at full speed.
    sleep: float = 1.5
    #: Determine preferred call direction, Outgoing is 0 and Received is 1.
    direction: float = 0.5
    #: Number of phone lines.
    lines: int = 3
    #: Number of extensions.
    exts: int = 20
    #: Max time in seconds the ring can be.
    max_ring: int = 20
    #: Max time in seconds the duration can be.
    max_duration: int = 7200
    #: The chance that a duration will be 0(unanswered), 1 in {value} chance.
    answered_chance: int = 5
    #: The chance that a call will be transferred, 1 in {value} chance.
    transferred_chance: int = 5
    #: Extension that will auto forward calls
    ext_forward: int = 105

    # noinspection PyMethodMayBeStatic
    def rand_number(self) -> str:
        return random.choice(callset)

    def rand_line(self) -> int:
        return random.randrange(1, self.lines + 1)

    def rand_ext(self) -> int:
        return random.randrange(100, 100 + self.exts)

    def rand_ring(self) -> int:
        return random.randrange(1, self.max_ring)

    def rand_duration(self) -> int:
        return 0 if random.randrange(self.answered_chance) == 0 else random.randrange(0, self.max_duration)

    def record(self, call_type: int) -> Record:
        record = Record(call_type=call_type)
        record.number = self.rand_number()
        record.line = self.rand_line()
        record.ext = self.rand_ext()
        record.ring = self.rand_ring()
        record.duration = self.rand_duration()
        return record

    def entrypoint(self) -> NoReturn:
        while self.is_running:
            # Deside if call is Outgoing or Received
            if random.random() > self.direction:
                self.outgoing()
            else:
                self.received()

            # Sleep between records if requested
            if self.sleep:
                time.sleep(self.sleep)

    def outgoing(self):
        record = self.record(call_type=Record.OUTGOING)
        self.push(record)

        if random.randrange(self.transferred_chance) == 0:
            # Randomly choose internal or external transfer
            record.ext = self.rand_ext()
            if random.randrange(2):
                record.call_type = Record.OUTGOING_TRANSFERRED_INT
            else:
                record.call_type = Record.OUTGOING_TRANSFERRED_EXT
            self.push(record)

    def received(self):
        record = self.record(call_type=Record.RECEIVED)

        # If we are sleeping before the next record
        # We want to add the Incoming records
        if self.sleep:
            # Use the ring time to select the delay
            # and number of hops before call ends
            for hop in range(int(record.ring / 4)):
                record.call_type = Record.INCOMING
                record.ext = self.rand_ext()
                self.push(record)
                time.sleep(hop)

        # Mock an extension with auto fowarding enabled
        if record.ext == self.ext_forward:
            record.call_type = Record.RECEIVED_FORWARDED
            self.push(record)

        # Mock a transferred call
        elif random.randrange(self.transferred_chance) == 0:
            record.call_type = Record.RECEIVED
            self.push(record)

            # Randomly choose internal or external transfer
            record.ext = self.rand_ext()
            if random.randrange(2):
                record.call_type = Record.RECEIVED_TRANSFERRED_INT
            else:
                record.call_type = Record.RECEIVED_TRANSFERRED_EXT
            self.push(record)
        else:
            record.call_type = Record.RECEIVED
            self.push(record)

# TODO: Add support for OUTGOING_FORWARDED and OUTGOING_VIA_FORWARDED
