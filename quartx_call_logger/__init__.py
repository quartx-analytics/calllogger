# Standard library
import logging
import sys
import os


class CusstomStreamHandler(logging.StreamHandler):
    """
    A handler class which writes logging records, appropriately formatted, to a stream.
    Debug & Info records will be logged to sys.stdout, and all other records will be logged to sys.stderr.
    """

    # noinspection PyBroadException
    def emit(self, record):
        """Swap out the stderr stream with stdout if log level is DEBUG or INFO."""
        if record.levelno <= 20:
            org_stream = self.stream
            self.stream = sys.stdout
            try:
                super(CusstomStreamHandler, self).emit(record)
            finally:
                self.stream = org_stream
        else:
            super(CusstomStreamHandler, self).emit(record)


# Configure the logging
cli_handler = CusstomStreamHandler()
cli_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
cli_handler.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(cli_handler)
logger.setLevel(logging.INFO)
