# Standard lib
from collections.abc import MutableMapping
from typing import Iterator


class Record(MutableMapping):
    """
    This class is a dictionary like object, subclassed from MutableMapping.

    Fields that are common to all call types.

        * **call_type** (*int*) - The type of call record, incoming/received/outgoing
        * **line** (*int*) - The line number that the call is on.
        * **ext** (*int*) - The extention number that the call is on.
        * **number** (*str*) - (*optional*) The phone number of the caller. If not givin, '+353000000000' is used.
        * **date** (*datetime*) - (*optional*) The datetime of the call, optional but recommended.

    Extra fields that are used for Received & Outgoing calls:

        * **ring** (*int*) - (*optional*) The time in seconds that the caller was ringing for. Defaults = 0
        * **duration** (*int*) - (*optional*) The duration of the call in seconds. Defaults = 0
        * **answered** (*int*/*bool*) - (*optional*) Indicate if call was answered. Determined by duration if not given.

    .. note:: **duration** & **ring** may also be in the format of ``HH:MM:SS``.

    .. note:: **date** must be in the ISO 8601 format e.g. ``2019-08-11T01:49:49+00:00``. UTC is preferred.

    There are 10 possible call types. Currently only the first 3 are processed, this will change in the future
    when we have more data to determine best way to process them.:

        * **0** Incoming call.
        * **1** Received call.
        * **2** Outgoing call.
        * **3** Received call (Other Service).
        * **4** Outgoing call (Other Service).
        * **5** Received call (Farwarded).
        * **6** Outgoing call (Farwarded).
        * **7** Received conference call.
        * **8** Outgoing conference call.
        * **9** Outgoing call Via Farwarded.

    :param kwargs: Any field can be passed in as a keyword argument
    """

    def __init__(self, **kwargs):
        self.data = dict(kwargs)

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
