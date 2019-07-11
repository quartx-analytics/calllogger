# Standard library
import configparser
import logging
import sys
import os

# Third party
from systemd import daemon
import appdirs

# Location for user config files and logs
CONFIG_DIR = appdirs.site_config_dir("call-logger")


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


cli_handler = CusstomStreamHandler()
cli_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
cli_handler.setLevel(logging.INFO)
logger = logging.getLogger("call_logger")
logger.addHandler(cli_handler)
logger.setLevel(logging.DEBUG)

# Config file paths
base_config = os.path.join(os.path.dirname(__file__), "data", "base-settings.ini")
user_config = os.path.join(CONFIG_DIR, "config.ini")

config = configparser.ConfigParser()
config.read([base_config, user_config])

daemon.notify('READY=1')
