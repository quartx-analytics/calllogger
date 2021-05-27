# Standard Lib
from typing import Union
import logging
import sys
import os

# Third Party
from getmac import get_mac_address

# Local
from calllogger import api, utils
from calllogger.conf import settings

__all__ = ["get_token", "revoke_token", "get_identifier"]
logger = logging.getLogger(__name__)
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
        if token := api.link_device(identifier):
            utils.write_datastore(token_store, token)
            logger.debug("Writing token to datastore")
            return token
        else:
            print("Unable to register device.")
            # TODO: Look into better exit code for link device
            sys.exit(1)
    else:
        if identifier is None:
            logger.info("Device registration unavailable. Missing required device identifier")
        if not settings.reg_key:
            logger.info("Device registration unavailable. Missing required registration key")

        print("Unable to proceed, missing required TOKEN.")
        print("Please set the TOKEN environment variable")
        sys.exit(0)


def revoke_token():
    """Remove token form datastore if exists."""
    logger.info("Removing stored token if exists")
    token_store.unlink(missing_ok=True)
