# Standard lib
from urllib import parse as urlparse
from typing import Iterator
import itertools
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

    def __init__(self, call_queue: queue.SimpleQueue, token: TokenAuth):
        super().__init__(suppress_errors=True, name=f"Thread-{self.__class__.__name__}")
        logger.info("Initializing CDR queue monitoring")
        logger.info("Sending CDRs to: %s", settings.domain)
        self.backlog_mode = False
        self.queue = call_queue
        self.logger = logger

        # Request
        self.request = requests.Request(
            method="POST",
            url=cdr_url,
            auth=token,
        )

    def entrypoint(self):
        """Process the call record queue."""

        while not self.stopped.is_set():
            # Deside if we need to switch to backlog mode
            if self.queue.qsize() > settings.backlog_trigger:
                self.backlog_mode = True

            # Process only at most the batch size of records
            records = self.process_queue(self.queue)
            records = list(itertools.islice(records, settings.batch_size))

            # We only send records in batches when in backlog mode
            # This is cause the server ignores errors for bulk requests
            if records and self.backlog_mode:
                self.send_request(self.request, records)
            else:
                for record in records:
                    self.send_request(self.request, record)

    def process_queue(self, record_queue) -> Iterator:
        """Keep yielding call records until queue is empty."""
        try:
            while record := record_queue.get(timeout=0.1):
                # In backlog mode we ignore incoming calls
                if self.backlog_mode and str(record.call_type) == str(record.INCOMING):
                    continue

                yield record.__dict__

        except queue.Empty:
            self.backlog_mode = False
