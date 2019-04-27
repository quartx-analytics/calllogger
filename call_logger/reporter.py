# Standard library imports
import threading
import functools
import queue
import time

# Third party imports
import requests

# Package imports
from . import plugins, config, logger


def spawn_reporters():
    """functools.partial(Reporter, args.key)"""
    # Find all frontends
    for frontend in config:
        if frontend.lower().startswith("frontend"):
            data = config[frontend]

            if "host" in data and "port" in data and "token" in data:
                yield functools.partial(Reporter, data["host"], data["port"], data["token"])
            else:
                logger.error(f"Frontend \"{frontend}\" is missing required parameters.")
                logger.error(f"Expected: 'host', 'port' 'token'")
                logger.error(f"Got: {list(data.keys())}")


class Reporter(threading.Thread):
    """Threaded class to monitor a queue for call logs and send the log to the frontend server."""
    def __init__(self, host: str, port: str, token: str, call_queue):
        super().__init__()

        # The base api url
        self.base_url = base_url = f"http://{host}:{port}/api/v1/"
        self.timeout = config["settings"].getint("timeout") * 60
        self.calls = call_queue
        self.token = token

        logger.debug(f"Frontend API url: {base_url}")

    def run(self):
        """Send queued up call logs to the frontent."""
        # Setup requests session
        session = requests.Session()
        session.headers["Authorization"] = f"Token {self.token}"
        session.headers["Content-Type"] = "application/json; charset=utf-8"
        session.headers["Accept"] = "application/json"
        self.clear_incoming(session)

        while True:
            # Fetch the call record from the queue
            record: plugins.Call = self.calls.get()

            try:
                resp = self.send_request(session, record)
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.exception(e)

                # There is no point in saving incoming records for later processing
                # sense the incoming call would have ended by then
                if record == 0:
                    logger.debug(f"Ignoring Incoming record: {record}")
                else:
                    # Send the record back for later logging
                    try:
                        self.calls.put_nowait(record)
                    except queue.Full:
                        logger.debug(f"Throwing away record: {record}")

                # Sleep for a specified amount of time
                # before reattempting connection
                if not isinstance(e, requests.Timeout):
                    self.sleep()

            else:
                # Check if response was actually accepted
                self.check_status(resp, record)

            # Record has been logged
            self.calls.task_done()

    def send_request(self, session: requests.session, record: plugins.Call) -> requests.Response:
        """
        Fist send a put request to update a incoming record.
        But if frontent respons with a status code of 404, then
        Send a post request to create the incoming record.
        """
        url = self.base_url + ("incoming/" if record.call_type == plugins.INCOMING else "call/")
        return session.post(url, json=record.data, timeout=self.timeout)

    def check_status(self, resp: requests.Response, record):
        """Check the status of the response, logging any errors."""
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            logger.error(e)
            logger.error(resp.text)
            logger.error(record)
            self.sleep()

    def sleep(self):
        logger.debug(f"Reattempting connection in: {self.timeout} seconds")
        time.sleep(500)

    def clear_incoming(self, session):
        """Send a command to clean the incoming call table."""
        try:
            url = self.base_url + "incoming/clear/"
            session.delete(url, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.error(e)
