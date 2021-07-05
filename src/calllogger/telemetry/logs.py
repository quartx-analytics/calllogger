# Standard Lib
import logging

# Third Party
from fluent import handler as fluent_handler

# Local
from calllogger import settings

logger = logging.getLogger("calllogger")


def setup_remote_logs(token: str, client: str):
    # noinspection PyTypeChecker
    formatter = fluent_handler.FluentRecordFormatter(dict(
        logger='%(name)s',
        level='%(levelname)s',
        thread="%(threadName)s",
        identifier=settings.identifier,
        client=client,
    ))
    handler = fluent_handler.FluentHandler(
        tag="calllogger",
        host="localhost",
        port=24224,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
