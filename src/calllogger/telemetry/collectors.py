# Standard Lib
import collections

# Local
from .point import Point
from calllogger import settings


class InfluxCollector:
    """Registry will manage the communication with the influxdb server."""

    def __init__(self):
        self.queue = collections.deque(maxlen=settings.queue_size)
        self.default_fields = {}
        self.default_tags = {}
        self.precision = "ns"

    # noinspection PyProtectedMember
    def write(self, point: Point):
        """Send influx metric to server."""
        point._fields.update(self.default_fields)
        line = point.to_line_protocol()
        if line:
            self.queue.append(line)
