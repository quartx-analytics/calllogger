# Standard Lib
from pathlib import PosixPath
import logging
import os

# Third Party
from requests.auth import AuthBase
from cryptography.fernet import Fernet

# Local
from calllogger.api import link_device

stored_token = PosixPath("/data/token")
encryption_key = b'haef_Qbi7Q8-qs7nQFWaySQWMe3YuA0ds8oJw5DObuY='
device_id = "258A3H"

logger = logging.getLogger(__name__)


class TokenAuth(AuthBase):
    """Requests Token authentication class."""

    def __init__(self):
        # Option 1: Environment Variable
        if "TOKEN" in os.environ:
            logger.debug("Loading token from environment variable.")
            self.__token = os.environ["TOKEN"]

        # Option 2: Stored locally
        elif stored_token.exists():
            logger.debug("Loading token from datastore.")
            self.__token = read_token(stored_token)

        # Option 3: Register with server
        else:
            logger.debug("Registering device with server.")
            self.__token = link_device(device_id)
            # write_token(stored_token, self.__token)
            logger.debug("Device token received, writing to datastore.")

    def __call__(self, req):
        req.headers["Authorization"] = f"Token {self.__token}"
        return req


def read_token(path: PosixPath) -> str:
    """Decrypt stored token and return."""
    crypto = Fernet(encryption_key)
    with path.open("rb") as stream:
        encrypted_token = stream.read()
        decrypted_token = crypto.decrypt(encrypted_token)
        return decrypted_token.decode("ASCII")


def write_token(path: PosixPath, token: str):
    """Encrypt token and save to disk."""
    crypto = Fernet(encryption_key)
    with path.open("wb") as stream:
        decrypted_token = token.encode("ASCII")
        encrypted_token = crypto.encrypt(decrypted_token)
        stream.write(encrypted_token)
