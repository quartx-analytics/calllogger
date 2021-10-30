# Standard Lib
import collections
import logging

# Local
from .point import Point
from calllogger import settings

logger = logging.getLogger(__name__)


class InfluxCollector:
    """Registry will manage the communication with the influxdb server."""

    def __init__(self, org: str, bucket: str):
        self.queue = collections.deque(maxlen=settings.queue_size)
        self.default_fields = {}
        self.default_tags = {}
        self.precision = "ns"
        self.bucket = bucket
        self.org = org

    # noinspection PyProtectedMember
    def write(self, point: Point):
        """Send influx metric to server."""
        point._fields.update(self.default_fields)
        line = point.to_line_protocol()
        if line:
            self.queue.append(line)
