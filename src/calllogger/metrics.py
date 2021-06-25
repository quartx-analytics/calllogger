# Standard Lib
from urllib.parse import urlparse

# Third party
import requests

# Local
from calllogger.influx import InfluxRegistry, Metric, Counter, Histogram


def track_http_request_errors(request: requests.PreparedRequest):
    """Track requests connection errors."""
    http_errors_counter(tags=dict(
        endpoint=urlparse(request.path_url).path,
        code="",
    )).inc()


def track_http_status_errors(resp: requests.Response):
    """Track requests http errors."""
    http_errors_counter(tags=dict(
        endpoint=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    )).inc()


def track_http_resp_time(resp: requests.Response):
    """Track requests response time."""
    request_time(tags=dict(
        endpoint=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    )).observe(
        resp.elapsed.total_seconds()
    )


# We instantiate the registry here so
# we can call connect from anywhere
collector = InfluxRegistry(
    url="https://influxdb.tools.quartx.dev",
    org="quartx",
    bucket="calllogger",
)

# Number of CDR processed
cdr_processed_counter = Counter.setup("calllogger_cdr_processed", collector)
# Number of serial errors
serial_error_counter = Counter.setup("calllogger_serial_error", collector)
# Number of http errors
http_errors_counter = Counter.setup("calllogger_http_errors", collector)

# Request latency
request_time = Histogram.setup("calllogger_http_request_duration_seconds", collector)

# System metrics like Ram, Swap, CPU
system_stats = Metric.setup("calllogger_system_stats", collector)
# Process metrics like ram and cpu usage
process_stats = Metric.setup("calllogger_process_stats", collector)
