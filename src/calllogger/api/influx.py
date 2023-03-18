# Standard lib
from urllib import parse as urlparse
import threading
import logging

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

    def __init__(
        self,
        url: str,
        org: str,
        bucket: str,
        collector: telemetry.InfluxCollector,
        token: str,
        default_tags=None,
        default_fields=None,
    ):
        super().__init__(system_collector=collector, suppress_errors=True, name=f"Thread-{self.__class__.__name__}")
        logger.info("Initializing InfluxDB metrics monitoring")
        self.collector = collector
        self.logger = logger
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
                org=org,
                bucket=bucket,
                precision=collector.precision,
            ),
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

        # Extrack upto the max of 250 metric lines
        # This is the recommended ammount by influxdata
        try:
            for _ in range(250):  # pragma: no branch
                line = self.collector.queue.popleft()
                lines.append(line)

        # We use the exception here to
        # just break from the loop
        except IndexError:
            pass

        # We may not have any metrics to upload yet
        if lines:
            self.request.data = "\n".join(lines)
            self.send_request(self.request, timeout=20.0)

    def handle_unauthorized(self, resp: requests.Response):
        """Quit submiting metrics if the token is no longer valid."""
        # We only want to quit sending metrics not quit the program
        self.logger.info(
            "Quitting as the Influx token does not have the required permissions or has been revoked.",
            extra={
                "url": resp.url,
                "status_code": resp.status_code,
                "reason": resp.reason,
            },
        )
        self.quit = True
