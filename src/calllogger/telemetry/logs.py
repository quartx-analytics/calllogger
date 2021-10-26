# Standard Lib
import logging

# Third Party
from logzio.handler import LogzioHandler

# Local
from calllogger import settings

logger = logging.getLogger("calllogger")
FLUENT_ADDRESS = "localhost"
FLUENT_PORT = 24224


def send_logs_to_logzio(client_info):
    handler = LogzioHandler(
        token=client_info["logzio_token"],
        logzio_type="calllogger",
        logs_drain_timeout=5,
        url=client_info["logzio_listener_url"],
        debug=settings.debug,
        backup_logs=False,
    )
    logger.addHandler(handler)
