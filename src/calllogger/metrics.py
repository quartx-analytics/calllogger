# Prometheus Types
from prometheus_client import Histogram
from prometheus_client import Counter


# Counters
serial_conn_error_counter = Counter(
    "serial_conn_error",
    "Number of serial connection errors"
)
serial_read_error_counter = Counter(
    "serial_read_error",
    "Number of serial read errors"
)
failed_decode_counter = Counter(
    "failed_decode",
    "Number of lines that failed to decode"
)
failed_validation_counter = Counter(
    "failed_validation",
    "Number of lines that failed validation"
)
failed_parse_counter = Counter(
    "failed_parse",
    "Number of lines that failed to parse"
)
empty_line_counter = Counter(
    "empty_line",
    "Number of empty serial lines"
)


# Histograms
request_time_histogram = Histogram(
    "http_request_duration_seconds",
    "Request latency"
)
