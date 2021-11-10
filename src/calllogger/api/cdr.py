# Standard lib
from urllib import parse as urlparse
import logging
import queue

# Third party
import requests

# Local
from calllogger.misc import ThreadExceptionManager
from calllogger.record import CallDataRecord
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
            if self.queue.qsize() <= settings.batch_trigger:
                try:
                    record: CallDataRecord = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                else:
                    self.send_request(self.request, record.__dict__)

            else:
                batch_jobs = []
                try:
                    # Extrack up to the max limit of records per batch job
                    while len(batch_jobs) < settings.batch_size:
                        record: CallDataRecord = self.queue.get(timeout=0.1)
                        # In batch mode we ignore incoming calls
                        # They make no sence in a batch job
                        if str(record.call_type) != str(record.INCOMING):
                            batch_jobs.append(record.__dict__)

                except queue.Empty:
                    # We use the Empty exception as a
                    # way to break from the loop
                    pass

                # This is needed to catch the rare time when
                # We only have incoming calls in the queue witch are ignored
                if batch_jobs:
                    self.send_request(self.request, batch_jobs, timeout=20)
