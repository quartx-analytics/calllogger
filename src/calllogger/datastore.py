# Standard Lib
from pathlib import PosixPath
import logging
import os

# Third Party
from cryptography.fernet import Fernet

# Local
from calllogger import api
from calllogger.conf import settings

__all__ = ["get_token"]
logger = logging.getLogger(__name__)
token_store = settings.datastore.joinpath("token")


def read_datastore(path: PosixPath, encoding="UTF8") -> str:
    """Decrypt stored token and return."""
    crypto = Fernet(settings.datastore_key.encode("ASCII"))
    with path.open("rb") as stream:
        encrypted_data = stream.read()
        decrypted_data = crypto.decrypt(encrypted_data)
        return decrypted_data.decode(encoding)


def write_datastore(path: PosixPath, data: str, encoding="UTF8"):
    """Encrypt token and save to disk."""
    crypto = Fernet(settings.datastore_key.encode("ASCII"))
    with path.open("wb") as stream:
        decrypted_data = data.encode(encoding)
        encrypted_data = crypto.encrypt(decrypted_data)
        stream.write(encrypted_data)


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
    else:
        logger.debug("Registering device with server.")
        token = api.link_device()
        write_datastore(token_store, token)
        logger.debug("Device token received, writing to datastore.")
