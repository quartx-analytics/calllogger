# Standard lib
from urllib import parse as urlparse
from threading import Thread
import queue

# Third party
import requests
from sentry_sdk import capture_exception

# Local
from calllogger.api import QuartxAPIHandler
from calllogger.conf import settings, TokenAuth

# We keep the url here for easier testing
cdr_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/")


class CDRWorker(QuartxAPIHandler, Thread):
    """
    Threaded class to monitor the call record queue and send the records
    to the QuartX monitoring service.

    :param call_queue: The call record queue.
    :param token: The authentication token for the monitoring service.
    """

    def __init__(self, call_queue: queue.Queue, token: TokenAuth):
        super().__init__(suppress_errors=True, name=f"Thread-{self.__class__.__name__}")
        self.queue = call_queue

        # Request
        self.request = requests.Request(
            method="POST",
            url=cdr_url,
            headers={"content-type": "application/json"},
            auth=token,
        )

    def run(self):
        try:
            self.entrypoint()
        except Exception as err:
            capture_exception(err)
            return False
        else:
            return True
        finally:
            self.running.clear()

    def entrypoint(self):
        """Process the call record queue."""
        while self.running.is_set():
            try:
                record = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self.send_request(self.request, record)
            finally:
                self.queue.task_done()
