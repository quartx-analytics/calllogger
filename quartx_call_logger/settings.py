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

# The plugin that is use for communicating with the phone system
# noinspection PyTypeChecker
PLUGIN_SETTINGS = {}
PLUGIN_NAME = ""

# Authentication Token, used to authenticate with QuartX Call Monitoring
# noinspection PyTypeChecker
TOKEN = ""
