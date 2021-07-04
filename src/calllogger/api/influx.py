# Standard lib
from urllib import parse as urlparse
import threading
import logging
import queue

# Third party
import requests

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth, sleeper
from calllogger import metrics

# We keep the url here for easier testing
logger = logging.getLogger(__name__)


class InfluxWrite(metrics.SystemMetrics, QuartxAPIHandler, threading.Thread):
    """
    Threaded class to monitor the metrics queue and send the metrics
    to the InfluxDB write API.

    :param collector: The influx collector object.
    :param token: The authentication token for the influxdb service.
    """

    def __init__(self, collector: metrics.InfluxCollector, token: str, **default_fields):
        super().__init__(suppress_errors=True, name=f"Thread-{self.__class__.__name__}")
        logger.info("Initializing InfluxDB metrics monitoring")
        self.collector = collector
        self.quit = False

        # Add the default fields to the collector
        collector.default_fields.update(default_fields)

        # Request
        self.request = requests.Request(
            method="POST",
            url=urlparse.urljoin(collector.url, "/api/v2/write"),
            auth=TokenAuth(token),
            params=dict(
                org=collector.org,
                bucket=collector.bucket,
                precision=collector.precision,
            )
        )

    def run(self):
        """Process the call record queue."""
        # We will sleep by 58 seconds instead of the desired 60
        # This is because each cpu_percent command will take 1 second to complete
        while sleeper(58, self.running.is_set) and self.quit is False:
            # Gather extra metrics first
            self.gather_system_metrics()
            self.gather_process_metrics()
            self.submit_metrics()

    def submit_metrics(self):
        """Submit to metrics to influxdb."""
        lines = []

        # Extrack upto the max of 1000 metric lines
        # This is the recommended ammount by influxdata
        try:
            for i in range(1000):
                record = self.collector.queue.get_nowait()
                lines.append(record)

        # We use the exception here to
        # just break from the loop
        except queue.Empty:
            pass

        # We may not have any metrics to upload yet
        if lines:
            self.request.data = "\n".join(lines)
            self.send_request(self.request)

    def handle_unauthorized(self, response):
        """Quit submiting metrics if the token is no longer valid."""
        self.quit = True
