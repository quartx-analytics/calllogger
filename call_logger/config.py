# Standard lib
import logging
import yaml
import sys
import os

# Third party
import appdirs

# Location for user config files and logs
CONFIG_DIR = appdirs.site_config_dir("glaonna")
BASE_CONFIG = os.path.join(os.path.dirname(__file__), "data", "default.yml")
USER_CONFIG = os.path.join(CONFIG_DIR, "call-logger.yml")


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


def compile_settings() -> dict:
    # Configure the logging
    cli_handler = CusstomStreamHandler()
    cli_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
    cli_handler.setLevel(logging.INFO)
    logger = logging.getLogger("call_logger")
    logger.addHandler(cli_handler)
    logger.setLevel(logging.DEBUG)

    with open(BASE_CONFIG) as stream:
        settings = yaml.safe_load(stream.read())

    if os.path.exists(USER_CONFIG):
        with open(USER_CONFIG) as stream:
            custom_config = yaml.safe_load(stream.read())

            # Validate that token is set
            if "settings" not in custom_config or "token" not in custom_config["settings"]:
                raise RuntimeError("missing required token. please set token in config file: %s", USER_CONFIG)

            # Recursively update base config
            update_recursively(settings, custom_config)

    return settings
