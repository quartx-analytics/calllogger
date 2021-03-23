# Standard lib
from urllib import parse as urlparse
from threading import Event, Thread
from typing import Union, Dict
import logging
import queue

# Third party
import requests
from requests import codes
from sentry_sdk import push_scope, capture_exception

# Package
from calllogger.conf import settings, TokenAuth
from calllogger.utils import Timeout, decode_response

logger = logging.getLogger(f"{__name__}")
cdr_url = urlparse.urljoin(settings.domain, "/api/v1/monitor/cdr/")
Record = Dict[str, Union[str, int]]


class CDRWorker(Thread):
    """
    Threaded class to monitor the call record queue and send the records
    to the QuartX monitoring service.

    :param call_queue: The call record queue.
    :param running: Threading flag to state if the thread should continue working.
    :param token: The authentication token for the monitoring service.
    """

    def __init__(self, call_queue: queue.Queue, running: Event, token: TokenAuth):
        super().__init__(name=f"Thread-{self.__class__.__name__}")

        # Attributes
        self.timeout = Timeout(settings, self)
        self.queue = call_queue
        self._running = running

        # Session
        self.session = requests.Session()
        self.session.auth = token

    @property
    def is_running(self) -> bool:
        """Flag to indicate that everything is working and ready to keep monitoring."""
        return self._running.is_set()

    def run(self):
        try:
            self.entrypoint()
        except Exception as err:
            capture_exception(err)
            self._running.clear()
            # TODO: See whats the better option to do here, quick or try again
            raise

    def entrypoint(self):
        """Process the call record queue."""
        while self.is_running:
            with push_scope() as scope:
                try:
                    record: Record = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Keep retrying to push the record if request fails
                while self.push_record(record, scope) and self.is_running:
                    self.timeout.sleep()

                self.timeout.reset()
                self.queue.task_done()

    def push_record(self, record: Record, scope) -> bool:
        """Push the record to the cloud. Returning True if request needs to be retried."""
        try:
            resp = self.session.post(cdr_url, json=record, timeout=self.timeout.value)
            resp.raise_for_status()
        except Exception as err:
            # Server is unreachable, try again later
            if isinstance(err, (requests.ConnectionError, requests.Timeout)):
                logger.warning("Connection to server failed/timed out")
                retry = True

            # Check status code to deside what to do next
            elif isinstance(err, requests.HTTPError) and err.response:
                logger.warning("API request failed with status code: %s", err.response.status_code)
                scope.set_extra("response", decode_response(err.response))
                scope.set_extra("status_code", err.response.status_code)
                scope.set_extra("elapsed", err.response.elapsed)
                retry = self.status_check(err.response.status_code)
            else:
                # Unexpected error, Let sentry do the rest
                logger.warning(str(err))
                retry = False

            scope.set_extra("record", record)
            capture_exception(err)
            return retry

    def status_check(self, status_code) -> bool:
        """Check the status of the response, Returning True if request needs to be retried."""

        # Quit if not authorized
        if status_code in (codes.unauthorized, codes.payment_required, codes.forbidden):
            logger.info("Quitting as the token does not have the required permissions or has been revoked.")
            self._running.clear()

        # Server is expereancing problems, reattempting request later
        elif status_code in (codes.not_found, codes.request_timeout) or status_code >= codes.server_error:
            logger.warning("Server is experiencing problems.")
            return True
