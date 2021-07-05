# Standard Lib
import logging

# Third Party
from fluent.handler import FluentRecordFormatter, FluentHandler

# Local
from calllogger import settings, closeers

logger = logging.getLogger("calllogger")


def setup_remote_logs(client: str):
    # noinspection PyTypeChecker
    formatter = FluentRecordFormatter(dict(
        logger='%(name)s',
        level='%(levelname)s',
        thread="%(threadName)s",
        identifier=settings.identifier,
        client=client,
    ))
    handler = FluentHandler(
        tag="calllogger",
        host="localhost",
        port=24224,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    closeers.append(handler.close)
