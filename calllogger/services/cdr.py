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


class API(Thread):
    """
    Threaded class to monitor the call record queue and send the records
    to the QuartX monitoring service.

    :param call_queue: The call record queue.
    :param running: Threading flag to state if the thread should continue working.
    :param token: The authentication token for the monitoring service.
    """

    def __init__(self, call_queue: queue.Queue, running: Event, token: TokenAuth, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Attributes
        self.timeout = Timeout(settings)
        self.queue = call_queue
        self.running = running

        # Session
        self.session = requests.Session()
        self.session.auth = token

    def run(self):
        """Process the call record queue."""
        while self.running.is_set():
            with push_scope() as scope:
                try:
                    record: Record = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Keep retrying to push the record if request fails
                while self.push_record(record, scope):
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
            self.running.clear()

        # Server is expereancing problems, reattempting request later
        elif status_code in (codes.not_found, codes.request_timeout) or status_code >= codes.server_error:
            logger.warning("Server is experiencing problems.")
            return True
