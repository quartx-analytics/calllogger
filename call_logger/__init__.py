# Standard lib
import logging
import yaml
import sys
import os

# Third party
from systemd import daemon
import appdirs

__all__ = ["config"]

# Location for user config files and logs
CONFIG_DIR = appdirs.site_config_dir("glaonna")


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


def update_recursively(base, custom):
    """Recursively update a dict of configuration settings."""
    for key, val in custom.items():
        if isinstance(val, dict):
            update_recursively(base[key], val)
        else:
            base[key] = val


# Configure the logging
cli_handler = CusstomStreamHandler()
cli_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
cli_handler.setLevel(logging.INFO)
logger = logging.getLogger("call_logger")
logger.addHandler(cli_handler)
logger.setLevel(logging.DEBUG)

# Configuration
base_config = os.path.join(os.path.dirname(__file__), "data", "default.yml")
user_config = os.path.join(CONFIG_DIR, "call-logger.yml")

with open(base_config) as stream:
    config = yaml.safe_load(stream.read())

with open(user_config) as stream:
    custom_config = yaml.safe_load(stream.read())

    # Validate that token is set
    if "settings" not in custom_config or "token" not in custom_config["settings"]:
        raise RuntimeError("missing required token. please set token in config file: %s", user_config)

    # Recursively update base config
    update_recursively(config, custom_config)

# Notify systemd that we are ready
daemon.notify("READY=1")
