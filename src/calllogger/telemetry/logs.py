# Standard Lib
import logging

# Third Party
from logzio.handler import LogzioHandler

# Local
from calllogger import settings

logger = logging.getLogger("calllogger")
FLUENT_ADDRESS = "localhost"
FLUENT_PORT = 24224


class ExtraLogzioHandler(LogzioHandler):
    """
    Custom LogzioHandler with an extra parameter to add default extra fields to records.

    :param dict default_extras: Dict of extra fields to add to all records.
    """
    def __init__(self, *args, default_extras: dict = None, **kwargs):
        super(ExtraLogzioHandler, self).__init__(*args, **kwargs)
        self._default_extras = default_extras or {}

    def extra_fields(self, message):
        """Inject default extra fields into record."""
        extra_fields = super().extra_fields(message)
        for key, val in self._default_extras.items():
            extra_fields.setdefault(key, val)
        return extra_fields


def send_logs_to_logzio(url: str, token: str, extras: dict):
    handler = ExtraLogzioHandler(
        token=token,
        logzio_type="calllogger",
        url=url,
        debug=settings.debug,
        backup_logs=False,
        default_extras=extras,
    )
    logger.addHandler(handler)
