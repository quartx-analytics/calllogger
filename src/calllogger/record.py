# Standard lib
from datetime import datetime, timezone

# Third Party
import attr

__all__ = ["CallDataRecord"]


def strip_str(_, __, value):
    """Strip any white space from string values."""
    return value.strip() if isinstance(value, str) else value


@attr.s(auto_attribs=True, collect_by_mro=True, on_setattr=strip_str)
class CallDataRecord:
    # Class attributes
    call_type: int = attr.ib(init=True)
    date: datetime = attr.ib(init=False)
    number: str = attr.ib(init=False)
    contact_name: str = attr.ib(init=False)
    contact_email: str = attr.ib(init=False)
    line: int = attr.ib(init=False)
    ext: int = attr.ib(init=False)
    ext_name: str = attr.ib(init=False)
    ring: int = attr.ib(init=False)
    duration: int = attr.ib(init=False)
    answered: bool = attr.ib(init=False)

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
