# Standard Lib
from urllib.parse import urlparse
import time
import os

# Third party
from uptime import uptime
import requests
import psutil

# Local
from .instruments import Metric, Histogram, Event
from .collectors import InfluxCollector
from .logs import setup_remote_logs

# We need to instantiate the collector here so
# we can pass the collector to all metric classes
collector = InfluxCollector(
    url="https://influxdb.tools.quartx.dev",
    org="quartx",
    bucket="calllogger",
)


class SystemMetrics:
    """Monitor the system metrics like CPU usage, Memory usage, disk usage and swap usage."""

    def __init__(self, *args, **kwargs):
        super(SystemMetrics, self).__init__(*args, **kwargs)
        # We get the process here as we should still be in the main thread
        # We do not get the right pid if running in a thread
        self._process = psutil.Process(os.getpid())

        self.system_stats = Metric.setup("calllogger_system_stats", collector)
        self.process_stats = Metric.setup("calllogger_process_stats", collector)

    # noinspection PyMethodMayBeStatic
    def gather_system_metrics(self):
        # Extract system stats
        disk = psutil.disk_usage("/")
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu_percent = min(100, psutil.cpu_percent(interval=1))

        # Use influx fields to store the values
        self.system_stats(fields=dict(
            uptime=uptime(),
            disk_used=disk.used,
            disk_total=disk.total,
            ram_used=ram.used,
            ram_total=ram.total,
            swap_used=swap.used,
            swap_total=swap.total,
            cpu_percent=cpu_percent,
        )).write()

    # noinspection PyMethodMayBeStatic
    def gather_process_metrics(self):
        process_uptime = time.time() - self._process.create_time()
        cpu_percent = min(100, self._process.cpu_percent(interval=1))

        # Use influx fields to store the values
        self.process_stats(fields=dict(
            uptime=process_uptime,
            cpu_percent=cpu_percent,
            ram_uss=self._process.memory_full_info().uss,
            ram_rss=self._process.memory_full_info().rss,
        )).write()


def track_http_request_errors(request: requests.PreparedRequest):
    """Track requests connection errors."""
    http_errors_counter(tags=dict(
        endpoint=urlparse(request.path_url).path,
        code="",
    )).mark()


def track_http_status_errors(resp: requests.Response):
    """Track requests http errors."""
    http_errors_counter(tags=dict(
        endpoint=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    )).mark()


def track_http_resp_time(resp: requests.Response):
    """Track requests response time."""
    request_time(tags=dict(
        endpoint=urlparse(resp.request.path_url).path,
        code=resp.status_code,
    )).observe(
        resp.elapsed.total_seconds()
    )


# Number of serial errors
serial_error_counter = Event.setup("serial_error", collector)
# Number of http errors
http_errors_counter = Event.setup("http_errors", collector)

# Request latency
request_time = Histogram.setup("http_request_duration_seconds", collector)
