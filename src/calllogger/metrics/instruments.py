# Standard Lib
from functools import partial

# Local
from .point import Point
from .collectors import InfluxCollector


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


class Event(Metric):
    def mark(self):
        self.field("value", True)
        self.write()


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
        value = max(0, self.tracker.get(self._name, 1) - amount)
        self.field("value", value)
        self.tracker[self._name] = value
        self.write()

    def set(self, value):
        """Set to a given value."""
        self.field("value", value)
        self.tracker[self._name] = value
        self.write()


class Histogram(Metric):
    """
    Histograms track the size and number of events in buckets.

    You can use Histograms for aggregatable calculation of quantiles.
    """

    def observe(self, amount):
        """Observe the given amount."""
        clone = self.field("value", amount)
        clone.write()
