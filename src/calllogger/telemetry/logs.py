# Standard Lib
import threading
import logging
import socket

# Third Party
from fluent.handler import FluentRecordFormatter
from fluent.asynchandler import FluentHandler

# Local
from calllogger import settings, closeers

logger = logging.getLogger("calllogger")
FLUENT_ADDRESS = "localhost"
FLUENT_PORT = 24224


def service_available(address: str, port: int):
    """Check that service at given address is available."""
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result_of_check = a_socket.connect_ex((address, port))
    return result_of_check == 0


def setup_remote_logs(client: str, retry=0):
    if service_available(FLUENT_ADDRESS, FLUENT_PORT):
        # noinspection PyTypeChecker
        formatter = FluentRecordFormatter(dict(
            logger='%(name)s',
            level='%(levelname)s',
            thread="%(threadName)s",
            identifier=settings.identifier,
            client=client,
        ))
        handler = FluentHandler(
            queue_circular=True,
            tag="calllogger",
            host="localhost",
            port=24224,
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        closeers.append(handler.close)
        logger.info("Connection made to local fluent server.")
    elif retry < 5:
        logger.info("Local fluent server not available yet. Waiting...")
        threading.Timer(3, setup_remote_logs, args=[client, retry + 1])
