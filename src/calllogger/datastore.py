# Standard Lib
from pathlib import PosixPath
from typing import Union
import logging
import base64
import sys
import os

# Third Party
from getmac import get_mac_address

# Local
from calllogger import api
from calllogger.conf import settings

__all__ = ["get_token", "revoke_token", "get_identifier"]
logger = logging.getLogger(__name__)
token_store = settings.datastore.joinpath("token")
identifier_store = settings.datastore.joinpath("identifier")


def read_datastore(path: PosixPath, encoding="UTF8") -> str:
    """Decode stored data and return."""
    with path.open("rb") as stream:
        encoded_data = stream.read()
        decoded_data = base64.b64decode(encoded_data)
        return decoded_data.decode(encoding)


def write_datastore(path: PosixPath, data: str, encoding="UTF8"):
    """Encode data and save to disk."""
    with path.open("wb") as stream:
        decoded_data = data.encode(encoding)
        encoded_data = base64.b64encode(decoded_data)
        stream.write(encoded_data)


def get_identifier() -> Union[str, None]:
    """Get the unique identifier for this device."""
    # Stored locally
    if identifier_store.exists():
        logger.debug("Loading device identifier from datastore.")
        return read_datastore(identifier_store)

    # Fetch and save
    identifier = get_mac_address()
    if identifier and identifier != "00:00:00:00:00:00":
        logger.debug("Storing device identifier to datastore.")
        write_datastore(identifier_store, identifier)
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
        return read_datastore(token_store)

    # Option 3: Register with server
    elif (identifier := get_identifier()) and settings.reg_key:
        if token := api.link_device(identifier):
            write_datastore(token_store, token)
            logger.debug("Writing token to datastore")
            return token
        else:
            print("Unable to register device. Can not proceed. Quitting.")
            sys.exit(0)
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
