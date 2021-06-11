# Standard Lib
from urllib.parse import urlparse

# Third party
import requests

# Prometheus Types
from prometheus_client import Histogram, Counter


# Counters
cdr_processed_counter = Counter(
    name="calllogger_cdr_processed",
    documentation="Number of CDR processed",
)
serial_error_counter = Counter(
    name="calllogger_serial_error",
    documentation="Number of serial errors",
    labelnames=["error_type"]
)
http_errors_counter = Counter(
    name="calllogger_http_status_errors",
    documentation="Number of http errors",
    labelnames=["path", "code"]
)


# Histograms
request_time_histogram = Histogram(
    name="calllogger_http_request_duration_seconds",
    documentation="Request latency",
    labelnames=["path", "code"],
)


def track_http_request_errors(request: requests.PreparedRequest):
    """Track requests connection errors."""
    http_errors_counter.labels(
        path=urlparse(request.path_url).path,
        code="",
    ).inc()


def track_http_status_errors(resp: requests.Response):
    """Track requests http errors."""
    http_errors_counter.labels(
        path=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    ).inc()


def track_http_resp_time(resp: requests.Response):
    """Track requests response time."""
    request_time_histogram.labels(
        path=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    ).observe(
        resp.elapsed.total_seconds()
    )
