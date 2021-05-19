# Standard lib
from functools import cached_property
from pathlib import PosixPath
from typing import Union
import logging
import sys
import os

# Third Party
from decouple import config, undefined, UndefinedValueError
from getmac import get_mac_address
import appdirs

# Local
from calllogger import api, utils

__all__ = ["settings", "merge_settings", "get_token", "revoke_token", "get_identifier"]
logger = logging.getLogger(__name__)


def merge_settings(cls, settings_store: dict, prefix="", **defaults):
    # Merge class, instance and defaults together
    defaults_store = dict(**cls.__dict__, **defaults)
    prefix = f"{prefix}_" if prefix else ""
    settings_store.update(defaults)
    errors = []

    # Check if all settings with annotations have a environment variable set for them
    for key, cast in cls.__dict__.get("__annotations__", {}).items():
        default = defaults_store.get(key, undefined)
        env_key = f"{prefix}{key}"
        try:
            setting = config(env_key.upper(), default, cast)
            settings_store[key] = setting
        except UndefinedValueError:
            errors.append(f"Missing required environment variable: {env_key}")
        except (ValueError, TypeError):
            errors.append(f"Invalid type for setting '{env_key}', expecting '{cast.__name__}'")

    # Report any error to user and quit
    if errors:
        for msg in errors:
            print(msg)
        sys.exit()


class Settings:
    """
    Settings class that allows settings
    to be override by environment variables.
    """

    #: Environment name, e.g. 'testing', 'production'
    environment: str = "Testing"
    #: Timeout in seconds to sleep on errors.
    timeout: int = 3
    #: Multiplier that increases the timeout on continuous errors.
    timeout_decay: float = 1.5
    #: The max timeout can be after continuous decay.
    max_timeout: int = 300
    #: Size of the call queue
    queue_size: int = 1_000
    # The domain to send the call logs to, used in development.
    domain: str = "https://quartx.ie"
    #: Set to true to enable debug logging.
    debug: bool = False

    # Flag to indicate if program is dockerized
    dockerized: bool = False

    def __init__(self):
        merge_settings(self.__class__, self.__dict__)

    @cached_property
    def sentry_dsn(self) -> str:
        return utils.decode_env("SENTRY_DSN")

    @cached_property
    def reg_key(self) -> str:
        return utils.decode_env("REG_KEY")

    @cached_property
    def datastore(self) -> PosixPath:
        """The location for the datastore."""
        if locale := os.environ.get("DATA_LOCATION"):
            locale = PosixPath(locale).resolve()
        else:
            # Use appdirs to select datastore location if locale is not given
            locale = appdirs.user_data_dir("quartx-calllogger")
            locale = PosixPath(locale)

        logger.debug("Datastore Location: %s", locale)
        os.makedirs(locale, exist_ok=True)
        return locale

    @property
    def plugin(self):
        """The name of the plugin to use."""
        if "PLUGIN" in os.environ["PLUGIN"]:
            return os.environ["PLUGIN"]
        else:
            print("environment variable: PLUGIN")
            sys.exit()


settings = Settings()
token_store = settings.datastore.joinpath("token")
identifier_store = settings.datastore.joinpath("identifier")


def get_identifier() -> Union[str, None]:
    """Get the unique identifier for this device."""
    # Stored locally
    if identifier_store.exists():
        logger.debug("Loading device identifier from datastore.")
        return utils.read_datastore(identifier_store)

    # Fetch and save
    identifier = get_mac_address()
    if identifier and identifier != "00:00:00:00:00:00":
        logger.debug("Storing device identifier to datastore.")
        utils.write_datastore(identifier_store, identifier)
        return identifier
    else:
        return None


def get_token() -> str:
    # Option 1: Environment Variable
    if "TOKEN" in os.environ:
        logger.debug("Loading token from environment variable.")
        return os.environ["TOKEN"]

    # Option 2: Stored locally
    elif token_store.exists():
        logger.debug("Loading token from datastore.")
        return utils.read_datastore(token_store)

    # Option 3: Register with server
    elif (identifier := get_identifier()) and settings.reg_key:
        logger.debug("Registering device with server.")
        token = api.link_device(identifier)
        utils.write_datastore(token_store, token)
        logger.debug("Device token received, writing to datastore.")
        return token
    else:
        if identifier is None:
            logger.debug("Device registration unavailable. Missing required device identifier")
        if not settings.reg_key:
            logger.debug("Device registration unavailable. Missing required registration key")

        print("Unable to proceed, missing required TOKEN.")
        print("Please set the TOKEN environment variable")
        sys.exit(1)


def revoke_token():
    """Remove token form datastore if exists."""
    logger.info("Removing stored token if exists")
    token_store.unlink(missing_ok=True)
