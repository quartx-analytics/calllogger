# Standard lib
import threading
import queue
import time

# Third party imports
import requests

# Package imports
from .record import Record
from . import config, logger

token = config["settings"]["token"]
url = "https://glaonna.ie/cdr/record/"
timeout = config["settings"]["timeout"]
timeout_decay = config["settings"]["decay"]
timeout_max = config["settings"]["max_timeout"]


class API(threading.Thread):
    """Threaded class to monitor for call logs and send them to the monitoring service."""

    def __init__(self):
        super().__init__()
        self.timeout = timeout
        self.queue = queue.Queue(10_000)
        self.running = threading.Event()
        self.running.set()
        self.daemon = True

        # Setup requests session
        self.session = session = requests.Session()
        session.headers["Authorization"] = f"Token {token}"
        session.headers["Content-Type"] = "application/json; charset=utf-8"
        session.headers["Accept"] = "application/json"

    def log(self, record: Record):
        self.queue.put(record)

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

                # There is no point in saving incoming records for later processing
                # sense the incoming call would have ended by then
                if record.call_type == Record.INCOMING:
                    logger.debug(f"Ignoring Incoming record: {record}")
                else:
                    try:
                        # We can't wait to add to queue
                        # as this would cause a dead lock
                        record_queue.put_nowait(record)
                    except queue.Full:
                        logger.debug(f"Queue full, throwing away record: {record}")

                # Sleep for a specified amount of time
                # before reattempting connection
                if not isinstance(e, requests.Timeout):
                    self._sleep()

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
            logger.error(resp.status_code)
            logger.error(e)

            if resp.status_code in (401, 403):
                logger.info("Quiting as given token thoes not have access to create call logs.")
                self.running.clear()
            else:
                self._sleep()
        else:
            self.timeout = timeout

    def _sleep(self):
        logger.debug(f"Reattempting connection in: {self.timeout} seconds")
        time.sleep(self.timeout)
        self.timeout = min(timeout_max, self.timeout * timeout_decay)
