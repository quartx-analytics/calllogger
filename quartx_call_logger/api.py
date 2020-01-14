# Standard lib
from urllib import parse as urlparse
from typing import Dict
import threading
import logging
import queue
import time
import json

# Third party
import requests

# Package
from . import settings

logger = logging.getLogger(f"{__name__}")

# The call type that indecates the incoming call type
INCOMING = 0


class API(threading.Thread):
    """Threaded class to monitor for call logs and send them to the monitoring service."""

    def __init__(self, call_queue, running):
        self.timeout = settings.TIMEOUT
        super().__init__()

        self.queue = call_queue
        self.running = running

        # Set url
        self.url = urlparse.urlunsplit((
            "https" if settings.SSL else "http",  # scheme
            settings.DOMAIN,                      # netloc
            "/api/v1/monitor/cdr/",               # path,
            "",                                   # query
            "",                                   # fragment
        ))

        # Setup requests session
        self.session = session = requests.Session()
        session.headers["Authorization"] = f"Token {settings.TOKEN}"
        session.headers["Content-Type"] = "application/json; charset=utf-8"
        session.headers["Accept"] = "application/json"
        session.verify = settings.SSL_VERIFY

    def re_push(self, record: Dict):
        # There is no point in saving incoming records for later processing
        # sense the incoming call would have ended by then
        if record["call_type"] == INCOMING:
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
                record: Dict = record_queue.get(timeout=0.1).clean()
            except queue.Empty:
                continue

            try:
                resp = session.post(self.url, json=record, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                self.re_push(record)
                extra_context = {"record": record, "headers": session.headers, "exception": e}

                # Sleep for a specified amount of time before reattempting connection
                msg = f"Re-attempting connection in: {self.timeout} seconds"
                if isinstance(e, requests.Timeout):
                    logger.error("Connection to API Timeed out", extra=extra_context)
                    self._sleep(f"Request timed out, {msg}")
                else:
                    logger.error("Connection to API Failed", extra=extra_context)
                    self._sleep(msg)

            else:
                # Check if response was actually accepted
                self._check_status(resp, record)

            # Record has been logged
            self.queue.task_done()

    def _check_status(self, resp: requests.Response, record: Dict):
        """Check the status of the response, logging any errors."""
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            logger.info(f"API request failed with status code {resp.status_code}")
            extra_context = {
                "headers": self.session.headers,
                "status_code": resp.status_code,
                "record": record,
                "exception": e,
            }

            try:
                data = resp.json()
            except json.decoder.JSONDecodeError:
                logger.debug("Error response was not a valid json response.")
                if len(resp.content) <= 1000:
                    extra_context["response"] = resp.content
                    logger.info(resp.content)
            else:
                extra_context["response"] = data
                logger.info(data)

            # Quit if not authorized
            if resp.status_code in (401, 402, 403, 498, 499):
                logger.info("Quitting as the given token does not have permission to create call logs.")
                logger.error("Unauthorized API access.", extra=extra_context)
                self.running.clear()

            # Server is expereancing problems, reattempting request later
            elif resp.status_code in (404, 408) or resp.status_code >= 500:
                self.re_push(record)
                logger.error("Server is experiencing problems.", extra=extra_context)
                self._sleep(f"Re-attempting request in: {self.timeout} seconds")

            else:
                extra_context.pop("exception")
                logger.error(e, extra=extra_context)
        else:
            self.timeout = settings.TIMEOUT

    def _sleep(self, msg):
        logger.info(msg)
        time.sleep(self.timeout)
        self.timeout = min(settings.MAX_TIMEOUT, self.timeout * settings.DECAY)
