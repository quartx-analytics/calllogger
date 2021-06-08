# Standard Lib
from urllib.parse import urlparse

# Third party
import requests

# Prometheus Types
from prometheus_client import Histogram
from prometheus_client import Counter


# Counters
serial_conn_error_counter = Counter(
    name="serial_conn_error",
    documentation="Number of serial connection errors",
)
serial_read_error_counter = Counter(
    name="serial_read_error",
    documentation="Number of serial read errors"
)
decode_errors_counter = Counter(
    name="failed_decode",
    documentation="Number of lines that failed to decode",
)
validation_errors_counter = Counter(
    name="failed_validation",
    documentation="Number of lines that failed validation",
)
parse_errors_counter = Counter(
    name="failed_parse",
    documentation="Number of lines that failed to parse",
)
empty_line_counter = Counter(
    name="empty_line",
    documentation="Number of empty serial lines",
)
cdr_processed_counter = Counter(
    name="cdr_processed",
    documentation="Number of CDR processed",
)
http_request_errors_counter = Counter(
    name="http_request_errors",
    documentation="Number of http errors with status code",
    labelnames=["method", "endpoint"]
)
http_status_errors_counter = Counter(
    name="http_status_errors",
    documentation="Number of http errors with status code",
    labelnames=["method", "endpoint", "status_code"]
)


# Histograms
request_time_histogram = Histogram(
    name="http_request_duration_seconds",
    documentation="Request latency",
    labelnames=["method", "endpoint", "status_code"],
)


def track_http_request_errors(request: requests.PreparedRequest):
    """Track requests connection errors."""
    http_request_errors_counter.labels(
        method=request.method,
        endpoint=urlparse(request.path_url).path,
    ).inc()


def track_http_status_errors(resp: requests.Response):
    """Track requests http errors."""
    http_status_errors_counter.labels(
        method=resp.request.method,
        endpoint=urlparse(resp.request.path_url).path,
        status_code=resp.status_code,
    ).inc()


def track_http_resp_time(resp: requests.Response):
    """Track requests response time."""
    request_time_histogram.labels(
        method=resp.request.method,
        endpoint=urlparse(resp.request.path_url).path,
        status_code=resp.status_code,
    ).observe(
        resp.elapsed.total_seconds()
    )
