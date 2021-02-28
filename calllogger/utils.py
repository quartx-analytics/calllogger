import logging


class OnlyMessages(logging.Filter):
    """Filter out records that are less than the WARNING level."""
    def filter(self, record):
        return record.levelno < logging.WARNING
