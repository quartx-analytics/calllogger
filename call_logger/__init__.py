# Standard library
# from logging import handlers
from typing import List
import configparser
import logging
import sys
import os

# Third party
import appdirs

# Location for user config files and logs
USER_CONFIG = appdirs.user_config_dir("call-logger")
CONFIG_DIR = appdirs.site_config_dir("call-logger")


class CusstomStreamHandler(logging.StreamHandler):
    """
    A handler class which writes logging records, appropriately formatted, to a stream.
    Debug & Info records will be logged to sys.stdout, and all other records will be logged to sys.stderr.
    """

    def __init__(self):
        super(CusstomStreamHandler, self).__init__(sys.stdout)

    # noinspection PyBroadException
    def emit(self, record):
        """Swap out the stdout stream with stderr if log level is WARNING or greater."""
        if record.levelno >= 30:
            org_stream = self.stream
            self.stream = sys.stderr
            try:
                super(CusstomStreamHandler, self).emit(record)
            finally:
                self.stream = org_stream
        else:
            super(CusstomStreamHandler, self).emit(record)


class CustomParser(configparser.ConfigParser):
    """Custom config parser that adds support to fetch settings as a list."""
    # noinspection PyShadowingBuiltins, PyProtectedMember
    def getintlist(self, section, option, *, raw=False, vars=None, fallback=configparser._UNSET, **kwargs) -> List[int]:
        """
        A convenience method which coerces the option in the specified section to a list of values.
        Values must be separated by a ','.
        """
        return self._get_conv(section, option, self._convert_to_list, raw=raw, vars=vars, fallback=fallback, **kwargs)

    @staticmethod
    def _convert_to_list(values: str) -> List[int]:
        return [int(value.strip()) for value in values.split(",")]


# Setup logger to log to both the console and log file
logger = logging.getLogger("call_logger")

# logfile = os.path.join(USER_CONFIG, "call_logger.log")
# file_handler = handlers.RotatingFileHandler(logfile, encoding="utf8", maxBytes=1024*1024, backupCount=1, delay=True)
# file_handler.setFormatter(logging.Formatter("%(relativeCreated)-19s %(levelname)5s: %(message)s"))
# file_handler.setLevel(logging.DEBUG)

cli_handler = CusstomStreamHandler()
cli_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
cli_handler.setLevel(logging.INFO)

# logger.addHandler(file_handler)
logger.addHandler(cli_handler)
logger.setLevel(logging.DEBUG)

# Config file paths
base_config = os.path.join(os.path.dirname(__file__), "data", "base-settings.ini")
config = CustomParser()

# Windows:
# Linux: /etc/xdg/call-logger
user_config = os.path.join(CONFIG_DIR, "config.ini")


def setup_env():
    """Setup the logger environment and config files."""

    # Rollover the log file on restart
    # file_handler.doRollover()

    # Parse the config files
    config.read([base_config, user_config])


# Common Arguments
arguments = [
    {
        "args": [
            "-s",
            "--simulate"
        ],
        "kwargs": {
            "nargs": "?",
            "const": True,
            "help": "Simulate a real phone system by sending fake records."
        }
    },
    {
        "args": [
            "-d",
            "--delay"
        ],
        "kwargs": {
            "help": "The time delay in seconds between each face record when using the simulator. (default: 1)",
            "default": 1.0,
            "type": float
        }
    },
    {
        "args": [
            "-i",
            "--disable-incoming"
        ],
        "kwargs": {
            "action": "store_true",
            "help": "Disable incoming call records when using the simulator."
        }
    }
]
