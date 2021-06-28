# Standard Lib
from functools import partial
import logging
import queue

# Local
from calllogger.influx.point import Point

logger = logging.getLogger(__name__)


class InfluxCollector:
    """Registry will manage the communication with the influxdb server."""

    def __init__(self, url: str, org: str, bucket: str):
        self.queue = queue.SimpleQueue()
        self.default_fields = {}
        self.precision = "ns"
        self.bucket = bucket
        self.org = org
        self.url = url

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


class Metric(Point):
    @classmethod
    def setup(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)

    def __init__(self, name: str, collector: InfluxCollector, tags: dict = None, fields: dict = None):
        super(Metric, self).__init__(name)
        self._collector = collector
        self._tags = tags or {}
        self._fields = fields or {}

    def write(self):
        # Set time in nanoseconds
        self._collector.write(self.time())


class Counter(Metric):
    """A Counter tracks counts of events or running totals."""
    tracker: dict[str, int] = {}

    def inc(self, amount=1):
        """Increment by given value."""
        value = self.tracker.get(self._name, 0) + amount
        clone = self.field("value", value)
        self.tracker[self._name] = value
        clone.write()


class Gauge(Counter):
    """Gauge metric, to report instantaneous values."""

    def dec(self, amount=1):
        """Decrement gauge by the given amount."""
        value = max(0, self.tracker.get(self._name, 0) - amount)
        clone = self.field("value", value)
        self.tracker[self._name] = value
        clone.write()

    def set(self, value):
        """Set to a given value."""
        clone = self.field("value", value)
        clone.write()


class Histogram(Metric):
    """
    Histograms track the size and number of events in buckets.

    You can use Histograms for aggregatable calculation of quantiles.
    """

    def observe(self, amount):
        """Observe the given amount."""
        clone = self.field("value", amount)
        clone.write()
