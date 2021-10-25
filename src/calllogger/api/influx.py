# Standard lib
from urllib import parse as urlparse
import threading
import logging
import queue

# Third party
import requests

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth
from calllogger import telemetry

# We keep the url here for easier testing
logger = logging.getLogger(__name__)


class InfluxWrite(telemetry.SystemMetrics, QuartxAPIHandler, threading.Thread):
    """
    Threaded class to monitor the metrics queue and send the metrics
    to the InfluxDB write API.

    :param collector: The influx collector object.
    :param token: The authentication token for the influxdb service.
    :param default_fields: Dict of default fields to add to every point.
    :param default_tags: Dict of default tags to add to every point.
    """

    def __init__(self, url: str, collector: telemetry.InfluxCollector, token: str, default_tags=None, default_fields=None):
        super().__init__(system_collector=collector, suppress_errors=True, name=f"Thread-{self.__class__.__name__}")
        logger.info("Initializing InfluxDB metrics monitoring")
        self.collector = collector
        self.quit = False

        # Add the default fields to the collector
        if default_fields:
            collector.default_fields.update(default_fields)
        if default_tags:
            collector.default_tags.update(default_tags)

        # Request
        self.request = requests.Request(
            method="POST",
            url=urlparse.urljoin(url, "/api/v2/write"),
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
        # This is because each cpu_percent & process commands will take 2 second to complete
        while not self.stopped.wait(58) and self.quit is False:
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
            for i in range(1000):  # pragma: no branch
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
        # We only want to quit sending metrics not quit the program
        self.quit = True
