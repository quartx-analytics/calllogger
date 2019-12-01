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


def set_plugin(plugin_name: str, plugin_settings: Dict) -> NoReturn:
    """Set the Plugin settings and sentry contexts."""
    globals()["PLUGIN_SETTINGS"] = plugin_settings
    globals()["PLUGIN_NAME"] = plugin_name

    with configure_scope() as scope:
        scope.set_tag("plugin", plugin_name)
        for key, val in plugin_settings.items():
            scope.set_extra(key, val)


# Setup
#######

# Location for user config files and logs
CONFIG_DIR = appdirs.site_config_dir("quartx")
CONFIG_FILE = os.path.join(CONFIG_DIR, "call-logger.yml")

# Populate the settings from user config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as stream:
        _custom_config = yaml.safe_load(stream.read())

    # Validate that required settings are given
    if "settings" not in _custom_config:
        _msg = f"missing required settings. please set required settings in config file: {CONFIG_FILE}"
        raise RuntimeError(_msg)

    # Validate that the token is set
    if not _custom_config["settings"].get("token"):
        _msg = f"missing required token. please set token in config file: {CONFIG_FILE}"
        raise RuntimeError(_msg)

    # Validate that a plugin is specified
    if not _custom_config["settings"].get("plugin"):
        _msg = f"missing required plugin. please set which plugin to use in config file: {CONFIG_FILE}"
        raise RuntimeError(_msg)

    # Validate that settings exists for specified plugin
    if _custom_config["settings"]["plugin"] not in _custom_config:
        _plugin = _custom_config["settings"]["plugin"]
        _msg = f"missing required plugin settings. please set plugin settings " \
               f"for {_plugin} in config file: {CONFIG_FILE}"
        raise RuntimeError(_msg)

    # Populate values
    _plugin_name = _custom_config["settings"].pop("plugin")
    set_plugin(_plugin_name, _custom_config[_plugin_name])
    set_token(_custom_config["settings"].pop("token"))
    for _key, _val in _custom_config["settings"]:
        globals()[_key.upper()] = _val


# Settings
##########

# Domain to send Call Records to
DOMAIN = "quartx.ie"
SSL_VERIFY = True
SSL = True

# Timeout in seconds before re-attemping connection on failure
MAX_TIMEOUT = 300
TIMEOUT = 10
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
