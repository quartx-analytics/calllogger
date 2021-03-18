from datetime import datetime, timezone
from typing import Dict, Union


class CallDataRecord:
    """A Call Data Record."""

    def __init__(self, call_type):
        self.data: Dict[str, Union[int, bool, str]] = dict(
            call_type=int(call_type),
            date=datetime.now().astimezone(timezone.utc).isoformat()
        )

    def date(self, date: str, fmt: str = "%d.%m.%y%X", tz: timezone = timezone.utc):
        """
        Convert date to a datetime object before saving.

        .. note::
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
            https://docs.python.org/3/library/datetime.html#timezone-objects

        :param str date: The date string.
        :param str fmt: The format of the date string. Default = '%d.%m.%y%X'
        :param timezone tz: The timezone the date is from. Default = 'UTC'
        """
        if date := date.strip():
            self.data["date"] = datetime.strptime(date, fmt).astimezone(tz).isoformat()

    @property
    def call_type(self):
        """The type of call record."""
        return self.data["call_type"]

    @property
    def number(self) -> str:
        """The phone number of the caller."""
        return self.data["number"]

    @number.setter
    def number(self, value):
        if value := value.strip():
            self.data["number"] = value

    @property
    def line(self) -> Union[int, str]:
        """The line number that the call is on."""
        return self.data["line"]

    @line.setter
    def line(self, value):
        if isinstance(value, int) or (value := value.strip()):
            self.data["line"] = value

    @property
    def ext(self) -> Union[int, str]:
        """The extention number that the call is on."""
        return self.data["ext"]

    @ext.setter
    def ext(self, value):
        if isinstance(value, int) or (value := value.strip()):
            self.data["ext"] = value

    @property
    def ring(self) -> Union[int, str]:
        """The time in seconds that the call was ringing for."""
        return self.data["ring"]

    @ring.setter
    def ring(self, value):
        if isinstance(value, int) or (value := value.strip()):
            self.data["ring"] = value

    @property
    def duration(self) -> Union[int, str]:
        """The duration of the call in seconds."""
        return self.data["duration"]

    @duration.setter
    def duration(self, value):
        if isinstance(value, int) or (value := value.strip()):
            self.data["duration"] = value

    @property
    def answered(self) -> Union[int, bool, str]:
        """
        Indicate if call was answered. if not given, value is determined by the call duration.
        IF no duration is given, the answered state will be marked as unknown.
        """
        return self.data["answered"]

    @answered.setter
    def answered(self, value):
        # A Boolean is also considered an Integer
        if isinstance(value, int) or (value := value.strip()):
            self.data["answered"] = value

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.data)})"
