# Standard lib
from typing import Iterator


class Record(dict):
    """
    This class is a dictionary like object.

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
    """

    def __repr__(self):
        data = self.copy()
        call_type = data.pop("call_type")
        data = ", ".join([f"{name}={repr(value)}" for name, value in data.items()])
        return f"{self.__class__.__name__}(call_type={call_type}, {data})"

    def copy(self):
        return self.__class__(self)

    @property
    def call_type(self):
        return int(self["call_type"])

    def clean(self):
        """Return a copy of the data with empty strings removed."""
        return self.__class__({k: v for k, v in self.items() if v != ""})
