# Standard lib
from collections.abc import MutableMapping
from typing import Iterator


class Record(MutableMapping):
    """
    Common required fields.
    number, line, ext

    Fields required by Received & Outgoing call logs.
    ring, duration

    Optinal fields for Received & Outgoing call logs.
    answered, date
    """

    # Answered field
    NOT_ANSWERED = 0
    ANSWERED = 1
    VOICEMAIL = 2

    # Calltype field
    INCOMING = 0
    RECEIVED = 1
    OUTGOING = 2

    def __init__(self, calltype: int, **kwargs):
        self.call_type = calltype
        if calltype != self.INCOMING:
            if "call_type" not in kwargs:
                kwargs["call_type"] = calltype

        self.data = {}
        # Update the dict class
        self.update(kwargs)

    def __setitem__(self, k, v) -> None:
        self.data[k] = v

    def __delitem__(self, k) -> None:
        del self.data[k]

    def __getitem__(self, k):
        return self.data[k]

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator:
        return iter(self.data)

    def __repr__(self):
        data = ", ".join([f"{name}={repr(value)}" for name, value in self.items()])
        return f"{self.__class__.__name__}({self.call_type}, {data})"
