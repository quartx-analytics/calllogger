# Standard lib
from typing import Dict, NoReturn
import yaml
import os

# Third party
from sentry_sdk import configure_scope
import appdirs


def set_token(token: str) -> NoReturn:
    """Set the Token setting and sentry user identifier."""
    globals()["TOKEN"] = token

    with configure_scope() as scope:
        # noinspection PyDunderSlots, PyUnresolvedReferences
        scope.user = {"id": token}


def set_plugin(plugin_name: str, plugin_settings: Dict = None) -> NoReturn:
    """Set the Plugin settings and sentry contexts."""
    globals()["PLUGIN_SETTINGS"] = {} if plugin_settings is None else plugin_settings
    globals()["PLUGIN_NAME"] = plugin_name

    with configure_scope() as scope:
        scope.set_tag("plugin", plugin_name)
        if plugin_settings:
            for key, val in plugin_settings.items():
                scope.set_extra(key, val)


# Settings
##########

# Domain to send Call Records to
DOMAIN = "quartx.ie"
SSL_VERIFY = True
SSL = True

# Timeout in seconds before re-attemping connection on failure
MAX_TIMEOUT = 300
TIMEOUT = 3
DECAY = 1.5

# The plugin that is use for communicating with the phone system
# noinspection PyTypeChecker
PLUGIN_SETTINGS = {}
PLUGIN_NAME = ""

# Authentication Token, used to authenticate with QuartX Call Monitoring
# noinspection PyTypeChecker
TOKEN = ""

# The size of the call log queue. The queue is used to buffer
# call logs when the internet or server is down.
QUEUE_SIZE = 10_000
