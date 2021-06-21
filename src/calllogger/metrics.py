# Standard Lib
from urllib.parse import urlparse
from copy import deepcopy
import time

# Third party
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import PointSettings


class InfluxRegistry:
    """Registry will manage the communication with the influxdb server."""

    def __init__(self, url: str, org: str, bucket: str):
        self.client = self.write_api = None
        self.bucket = org
        self.org = bucket
        self.url = url
        self.point_settings = PointSettings()
        self._buffer: list[Point] = []

    def connect(self, token: str, identifier: str, client: str):
        """Make the connection to the InfluxDB server."""
        # Add default tags related to device and client
        self.point_settings.add_default_tag("id", identifier)
        self.point_settings.add_default_tag("client", client)

        self.client = client = InfluxDBClient(url=self.url, token=token, org=self.org, enable_gzip=True)
        self.write_api = client.write_api(point_settings=self.point_settings)

        # Send any buffered metrics to server
        self.write_many(*self._buffer)

    def write(self, point: Point):
        """Send influx metric to server."""
        if self.write_api is not None:
            self.write_api.write(bucket=self.bucket, record=point)
        else:
            # Buffer the metric so it can be sent
            # later when a connection is available
            self._buffer.append(point)

    def write_many(self, *points: Point):
        """Send influx metrics to server."""
        for point in points:
            self.write(point)

    def close(self):
        """Send any buffered metrics to server then close."""
        if self.write_api is not None:
            self.write_api.close()


# We instantiate the registry here so
# we can call connect from anywhere
collector = InfluxRegistry(
    url="https://influxdb.tools.quartx.dev",
    org="quartx",
    bucket="calllogger",
)


class Metric(Point):
    def __init__(self, name: str, registry: InfluxRegistry = collector):
        super(Metric, self).__init__(name)
        self._registry = registry

    # noinspection PyProtectedMember
    def _clone(self):
        clone = self.__class__(self._name, self._registry)
        clone.__dict__ = deepcopy(self.__dict__)
        return clone

    def time(self, *args, **kwargs):
        clone = self._clone()
        return super(Metric, clone).time(*args, **kwargs)

    def tag(self, *args):
        clone = self._clone()
        return super(Metric, clone).tag(*args)

    def tags(self, **kwargs):
        clone = self._clone()
        clone._tags.update(kwargs)
        return clone

    def field(self, *args):
        clone = self._clone()
        return super(Metric, clone).field(*args)

    def fields(self, **kwargs):
        clone = self._clone()
        clone._fields.update(kwargs)
        return clone

    def write(self):
        clone = self.time(time.time(), write_precision=WritePrecision.MS) if self._time is None else self
        self._registry.write(clone)


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
    tracker: dict[str, int] = {}

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


def track_http_request_errors(request: requests.PreparedRequest):
    """Track requests connection errors."""
    http_errors_counter.tags(
        endpoint=urlparse(request.path_url).path,
        code="",
    ).inc()


def track_http_status_errors(resp: requests.Response):
    """Track requests http errors."""
    http_errors_counter.tags(
        endpoint=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    ).inc()


def track_http_resp_time(resp: requests.Response):
    """Track requests response time."""
    request_time.tags(
        endpoint=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    ).observe(
        resp.elapsed.total_seconds()
    )


# Number of CDR processed
cdr_processed_counter = Counter("calllogger_cdr_processed")
# Number of serial errors
serial_error_counter = Counter("calllogger_serial_error")
# Number of http errors
http_errors_counter = Counter("calllogger_http_status_errors")

# Request latency
request_time = Histogram("calllogger_http_request_duration_seconds")

# System metrics like Ram, Swap and CPU usage
system_stats = Metric("calllogger_system_stats")
