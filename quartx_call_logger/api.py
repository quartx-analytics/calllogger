# Standard lib
from urllib import parse as urlparse
import threading
import logging
import queue
import time
import json

# Third party
import requests

# Package
from .record import Record
from . import settings

token = settings["settings"]["token"]
url = "http://quartx.ie/monitor/cdr/record/"
timeout = settings["settings"]["timeout"]
timeout_decay = settings["settings"]["decay"]
timeout_max = settings["settings"]["max_timeout"]
logger = logging.getLogger(f"{__name__}.api")

# Call types to ignore when there are errors
IGNORE_ON_ERROR = [Record.INCOMING]


def set_url(frontend_url):
    """Set the api url"""
    global url
    base = urlparse.urlsplit(url)
    new = urlparse.urlsplit(frontend_url)
    url = urlparse.urlunsplit((new.scheme, new.netloc, base.path, base.query, base.fragment))


class API(threading.Thread):
    """Threaded class to monitor for call logs and send them to the monitoring service."""

    def __init__(self, call_queue):
        super().__init__()
        self.running = threading.Event()
        self.queue = call_queue
        self.timeout = timeout
        self.running.set()
        self.daemon = True

        # Setup requests session
        self.session = session = requests.Session()
        session.headers["Authorization"] = f"Token {token}"
        session.headers["Content-Type"] = "application/json; charset=utf-8"
        session.headers["Accept"] = "application/json"
        session.verify = False

    def re_push(self, record: Record):
        # There is no point in saving incoming records for later processing
        # sense the incoming call would have ended by then
        if record.call_type in IGNORE_ON_ERROR:
            logger.debug(f"Ignoring Incoming record: {record}")
        else:
            try:
                # We can't wait to add to queue
                # as this would cause a dead lock
                self.queue.put_nowait(record)
            except queue.Full:
                logger.debug(f"Queue full, throwing away record: {record}")

    def run(self):
        """Send queued call logs to the monitoring server."""
        session = self.session
        record_queue = self.queue

        while self.running.is_set():
            try:
                # Fetch the call record from the queue
                record: Record = record_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                resp = session.post(url, json=record.data, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.error(e)
                self.re_push(record)

                # Sleep for a specified amount of time
                # before reattempting connection
                msg = f"Re-attempting connection in: {self.timeout} seconds"
                if isinstance(e, requests.Timeout):
                    self._sleep(f"Request timed out, {msg}")
                else:
                    self._sleep(msg)

            else:
                # Check if response was actually accepted
                self._check_status(resp, record)

            # Record has been logged
            self.queue.task_done()

    def _check_status(self, resp: requests.Response, record):
        """Check the status of the response, logging any errors."""
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            logger.error(record)
            logger.error(e)

            try:
                data = resp.json()
            except json.decoder.JSONDecodeError:
                logger.debug("error response was not a valid json response.")
                if len(resp.content) <= 100:
                    logger.error(resp.content)
            else:
                logger.error(data)

            # Quit if not authorized
            if resp.status_code in (401, 402, 403, 498, 499):
                logger.info("Quiting as given token thoes not have access to create call logs.")
                self.running.clear()
                return

            # Server is expereancing problems
            # Reattempt request later
            elif resp.status_code in (404, 408) or resp.status_code >= 500:
                self.re_push(record)
                self._sleep(f"Re-attempting request in: {self.timeout} seconds")
        else:
            self.timeout = timeout

    def _sleep(self, msg):
        logger.debug(msg)
        time.sleep(self.timeout)
        self.timeout = min(timeout_max, self.timeout * timeout_decay)
