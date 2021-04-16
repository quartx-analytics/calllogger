# Standard library
from typing import NoReturn
import random

# Local
from calllogger.utils import sleeper
from calllogger.plugins import BasePlugin
from calllogger.record import CallDataRecord as Record

# Set of predefined numbers to
# create mock calls from
callset = {
    "0857539075": "Michael Forde",
    "0873575643": "Tom Baker",
    "0853436640": "Jerry Cremin",
    "0277665604": "Louie Walsh",
    "0107974846": "Tim Barra",
    "0213268621": "Mike Twomey",
    "0850549045": "Philip Murray",
    "0877644458": "Maura Jenkins",
}
numbers = (
    "0667126317", "0667124800", "0667199999", "0214274845",
    "0214365241", "016643658", "0212355545", "018302044",
)
ext_names = {
    101: "Office",
    102: "Shop",
}

for number in numbers:
    callset[number] = None


class MockCalls(BasePlugin):
    """Generate random call records continuously."""

    #: Time in seconds to delay, 0 will skip incoming and push at full speed.
    sleep: float = 1
    #: Time in seconds to delay between incoming call hops.
    incoming_delay: float = 2
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
    #: The chance that a call will be transferred, 1 in {value} chance. 0 to disable.
    transferred_chance: int = 5
    #: Determine preferred transferred direction, Internal is 0 and External is 1.
    transferred_direction: float = 0.5
    #: Extension that will auto forward calls
    ext_forward: int = 105

    # noinspection PyMethodMayBeStatic
    def rand_number(self) -> str:
        return random.choice(list(callset))

    def rand_line(self) -> int:
        return random.randrange(1, self.lines + 1)

    def rand_ext(self) -> int:
        return random.randrange(100, 100 + self.exts)

    def rand_ring(self) -> int:
        return random.randrange(1, self.max_ring)

    def rand_duration(self) -> int:
        return 0 if random.randrange(self.answered_chance) == 0 else random.randrange(0, self.max_duration)

    # noinspection PyMethodMayBeStatic
    def add_ext_name(self, record):
        """Add extension name if exists."""
        if name := ext_names.get(record.ext):
            record.ext_name = name

    # noinspection PyMethodMayBeStatic
    def add_contact_name(self, record):
        """Add contact name if exists."""
        if name := callset[record.number]:
            record.contact_name = name

    def push(self, record: Record) -> NoReturn:
        """Add ext/contact names if available before pushing."""
        self.add_contact_name(record)
        self.add_ext_name(record)
        super().push(record)

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
                sleeper(self.sleep, lambda: self.is_running)

    def outgoing(self):
        # Push the normal outgoing record
        record = self.record(call_type=Record.OUTGOING)
        self.push(record)

        # Randomly add a transfered call
        if self.transferred_chance and random.randrange(self.transferred_chance) == 0:
            self.transfered_call(record)

    def received(self):
        record = self.record(call_type=Record.RECEIVED)

        # If we are sleeping before the next record
        # We want to add the Incoming records
        if self.sleep:
            self.incoming(record)

        # Mock a transferred call
        if self.transferred_chance and random.randrange(self.transferred_chance) == 0:
            record.call_type = Record.RECEIVED
            self.push(record)
            self.transfered_call(record)
        else:
            # Mock a forwarded call if ext is setup for auto forwarding, else normal received call
            record.call_type = Record.RECEIVED_FORWARDED if record.ext == self.ext_forward else Record.RECEIVED
            self.push(record)

    def incoming(self, record):
        # Use the ring time to select the delay
        # and number of hops before call ends
        for hop in range(int(record.ring / 4)):  # pragma: no branch
            record.call_type = Record.INCOMING
            record.ext = self.rand_ext()
            self.push(record)
            sleeper(self.incoming_delay, lambda: self.is_running)

    def transfered_call(self, record: Record):
        """Randomly choose between internal or external."""
        if random.random() > self.transferred_direction:
            record.call_type = Record.OUTGOING_TRANSFERRED_INT
        else:
            record.call_type = Record.OUTGOING_TRANSFERRED_EXT

        record.ext = self.rand_ext()
        self.push(record)


# TODO: Add support for OUTGOING_FORWARDED and OUTGOING_VIA_FORWARDED
# TODO: Add support for simulating auto attendant
# TODO: Add support for answering machines
