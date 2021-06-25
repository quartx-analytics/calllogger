# Standard Lib
from datetime import datetime
from functools import partial

# Third party
from influxdb_client import InfluxDBClient, Point


class InfluxRegistry:
    """Registry will manage the communication with the influxdb server."""

    def __init__(self, url: str, org: str, bucket: str):
        self.client = self.write_api = None
        self.bucket = bucket
        self.org = org
        self.url = url
        self.default_fields = {}

    def connect(self, token: str, **default_fields):
        """Make the connection to the InfluxDB server."""
        self.default_fields.update(default_fields)
        self.client = client = InfluxDBClient(url=self.url, token=token, org=self.org, enable_gzip=True)
        self.write_api = client.write_api()

    # noinspection PyProtectedMember
    def write(self, point: Point):
        """Send influx metric to server."""
        if self.write_api is not None:
            # Better to put the identifying data into fields, Better for performance
            point._fields.update(self.default_fields)
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def close(self):
        """Send any buffered metrics to server then close."""
        if self.write_api is not None:
            self.write_api.close()
            self.write_api = None
        if self.client is not None:
            self.client.close()
            self.client = None


class Metric(Point):
    @classmethod
    def setup(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)

    def __init__(self, name: str, collector: InfluxRegistry, tags: dict = None, fields: dict = None):
        super(Metric, self).__init__(name)
        self._collector = collector
        self._tags = tags or {}
        self._fields = fields or {}

    def tags(self, **kwargs):
        self._tags.update(kwargs)
        return self

    def fields(self, **kwargs):
        self._fields.update(kwargs)
        return self

    def write(self):
        if self._time is None:
            self.time(datetime.utcnow())
        self._collector.write(self)


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
