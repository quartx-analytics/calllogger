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
        * **answered** (*int*) (*optional*) Flag to indecate if the call was answered.
        * **date** (*datetime*) (*optional*) The datetime of the call, optional but recommended.

    .. note:: **duration** & **ring** may also be in the format of "hh:mm:ss".

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

    def __init__(self, calltype: int, **kwargs):
        self.call_type = calltype
        kwargs["call_type"] = calltype

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
        data = ", ".join([f"{name}={repr(value)}" for name, value in self.items()])
        return f"{self.__class__.__name__}({self.call_type}, {data})"

    def copy(self):
        return self.data.copy()
