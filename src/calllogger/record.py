# Standard lib
from datetime import datetime, timezone

# Third Party
import attrs

__all__ = ["CallDataRecord"]


def strip_str(_, __, value):
    """Strip any white space from string values."""
    return value.strip() if isinstance(value, str) else value


@attrs.define(on_setattr=strip_str, slots=False)
class CallDataRecord:
    """
    The dataclass is for call data records.

    All available Fields.

        * **call_type** (*int*) - The type of call record, incoming/received/outgoing
        * **line** (*int*) - The line number that the call is on.
        * **ext** (*int*) - The extention number that the call is on.
        * **number** (*str*) - The phone number of the caller. If not givin, '+353000000000' is used.
        * **date** (*datetime*) - The datetime of the call, optional but recommended.
        * **ring** (*int*) - The time in seconds that the caller was ringing for. Defaults = 0
        * **duration** (*int*) - The duration of the call in seconds. Defaults = 0
        * **answered** (*int*/*bool*) - Indicate if call was answered. Determined by duration if not given.
        * **raw** (*str*) - The original unparsed raw call record.

    .. note:: **duration** & **ring** may also be in the format of ``HH:MM:SS`` or ``MM:SS``.

    .. note:: **date** must be in the ISO 8601 format e.g. ``2019-08-11T01:49:49+00:00``. timezone info is required.

    All known/supported call types.

    :cvar INCOMING: 0
    :cvar RECEIVED: 1
    :cvar OUTGOING: 2
    :cvar RECEIVED_OTHER: 3 Unsupported (Don't know what it means)
    :cvar OUTGOING_OTHER: 4 Unsupported (Don't know what it means)
    :cvar RECEIVED_FORWARDED: 5
    :cvar OUTGOING_FORWARDED: 6
    :cvar RECEIVED_CONFERENCE: 7 Unsupported (Support coming soon).
    :cvar OUTGOING_CONFERENCE: 8 Unsupported (Support coming soon).
    :cvar OUTGOING_VIA_FORWARDED: 9
    :cvar RECEIVED_TRANSFERRED_INT: 35
    :cvar OUTGOING_TRANSFERRED_INT: 36
    :cvar RECEIVED_TRANSFERRED_EXT: 37
    :cvar OUTGOING_TRANSFERRED_EXT: 38
    """

    # Class attributes
    call_type: int = attrs.field(init=True)
    date: datetime = attrs.field(init=False)
    number: str = attrs.field(init=False)
    contact_name: str = attrs.field(init=False)
    contact_email: str = attrs.field(init=False)
    line: int = attrs.field(init=False)
    ext: int = attrs.field(init=False)
    ext_name: str = attrs.field(init=False)
    ring: int = attrs.field(init=False)
    duration: int = attrs.field(init=False)
    answered: bool = attrs.field(init=False)
    raw: str = attrs.field(init=False)

    # Class Vars
    INCOMING = 0
    RECEIVED = 1
    OUTGOING = 2
    RECEIVED_OTHER = 3
    OUTGOING_OTHER = 4
    RECEIVED_FORWARDED = 5
    OUTGOING_FORWARDED = 6
    RECEIVED_CONFERENCE = 7
    OUTGOING_CONFERENCE = 8
    OUTGOING_VIA_FORWARDED = 9
    RECEIVED_TRANSFERRED_INT = 35
    OUTGOING_TRANSFERRED_INT = 36
    RECEIVED_TRANSFERRED_EXT = 37
    OUTGOING_TRANSFERRED_EXT = 38

    # noinspection PyUnresolvedReferences
    @date.default
    def _default_date(self):
        return datetime.now(timezone.utc)

    def date_str(self, date: str, fmt: str = "%d.%m.%y%X", tz: timezone = timezone.utc):
        """
        Convert a date string to a datetime object before saving.

        .. note::
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
            https://docs.python.org/3/library/datetime.html#timezone-objects

        :param str date: The date string.
        :param str fmt: The format of the date string. Default = '%d.%m.%y%X'
        :param timezone tz: The timezone the date is from. Default = 'UTC'
        """
        if date := date.strip():
            self.date = datetime.strptime(date, fmt).replace(tzinfo=tz)

    def as_dict(self) -> dict:
        """Return this objects data as a dict of values."""
        return self.__dict__
