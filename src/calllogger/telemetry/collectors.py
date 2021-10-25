# Standard Lib
import logging
import queue

# Local
from .point import Point

logger = logging.getLogger(__name__)


class InfluxCollector:
    """Registry will manage the communication with the influxdb server."""

    def __init__(self, org: str, bucket: str):
        self.queue = queue.SimpleQueue()
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
        if line and self.queue.qsize() <= 1_000:
            self.queue.put(line)
        elif line:
            logger.debug("Metrics queue full: %s", line)
        else:
            logger.debug("Metrics line is empty")
