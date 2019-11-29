# Standard lib
from collections.abc import MutableMapping
from typing import Iterator


class Record(MutableMapping):
    """
    This class is a dictionary like object, subclassed from MutableMapping.

    The fields that are used for Incoming calls:

        * **number** (*str*) - The phone number of the call.
        * **line** (*int*) - The line number that the call is on.
        * **ext** (*int*) - The extention number that the call is on.

    The fields that are used for Received & Outgoing calls:

        * **number** (*str*) - The phone number of the call.
        * **line** (*int*) - The line number that the call is on.
        * **ext** (*int*) - The extention number that the call is on.
        * **ring** (*int*) - The time in seconds that the caller was ringing for.
        * **duration** (*int*) - The duration of the call in seconds.
        * **answered** (*int*/*bool*) (*optional*) Flag to indecate if the call was answered.
        * **date** (*datetime*) (*optional*) The datetime of the call, optional but recommended.

    .. note:: **duration** & **ring** may also be in the format of ``HH:MM:SS``.

    .. note:: **date** must be in the ISO 8601 format e.g. ``2019-08-11T01:49:49+00:00``. UTC is preferred.

    :cvar int NOT_ANSWERED:  Mark as not answered
    :cvar int ANSWERED:  Mark as answered
    :cvar int VOICEMAIL:  Mark as farwarded to voicemail

    :cvar int INCOMING:  Mark as an incoming call
    :cvar int RECEIVED:  Mark as a reveived call
    :cvar int OUTGOING:  Mark as a call outgoing call

    :param int calltype: The type of call record, incoming/reveived/outgoing
    :param kwargs: Any field can be passed in as a keyword argument
    """

    # Answered field
    NOT_ANSWERED = 0
    ANSWERED = 1
    VOICEMAIL = 2

    # Calltype field
    INCOMING = 0
    RECEIVED = 1
    OUTGOING = 2

    def __init__(self, **kwargs):
        self.data = {}
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
        data = self.data.copy()
        call_type = data.pop("call_type")
        data = ", ".join([f"{name}={repr(value)}" for name, value in self.items()])
        return f"{self.__class__.__name__}(call_type={call_type}, {data})"

    def copy(self):
        return self.data.copy()

    @property
    def call_type(self):
        return int(self.data["call_type"])

    def clean(self):
        """Remove values with empty strings."""
        return {k: v for k, v in self.data.items() if v != ""}
