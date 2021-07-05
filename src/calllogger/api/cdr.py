# Standard lib
from urllib import parse as urlparse
import logging
import queue

# Third party
import requests

# Local
from calllogger.misc import ThreadExceptionManager
from calllogger.api import QuartxAPIHandler
from calllogger.utils import TokenAuth
from calllogger import settings

# We keep the url here for easier testing
cdr_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/")
logger = logging.getLogger(__name__)


class CDRWorker(QuartxAPIHandler, ThreadExceptionManager):
    """
    Threaded class to monitor the call record queue and send the records
    to the QuartX monitoring service.

    :param call_queue: The call record queue.
    :param token: The authentication token for the monitoring service.
    """

    def __init__(self, call_queue: queue.Queue, token: TokenAuth):
        super().__init__(suppress_errors=True, name=f"Thread-{self.__class__.__name__}")
        logger.info("Initializing CDR queue monitoring")
        logger.debug("Sending CDRs to: %s", settings.domain)
        self.queue = call_queue

        # Request
        self.request = requests.Request(
            method="POST",
            url=cdr_url,
            auth=token,
        )

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
