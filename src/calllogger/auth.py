# Standard Lib
import logging
import sys

# Local
from calllogger import api, settings, utils
from calllogger.utils import TokenAuth

__all__ = ["get_token", "revoke_token"]
logger = logging.getLogger(__name__)
token_store = settings.datastore.joinpath("token")


def get_token() -> TokenAuth:
    """
    Fetch the CDR token the datastore. If no token is found then request token from server.
    """
    if token_store.exists():
        logger.debug("Loading token from datastore.")
        token = utils.read_datastore(token_store)
        return TokenAuth(token)

    else:
        # Option 3: Register with server
        token = request_token()
        return TokenAuth(token)


def request_token() -> str:
    """Request token from server. This won't be possible if we have no identifier."""
    if settings.reg_key:
        if token := api.link_device(settings.identifier):
            utils.write_datastore(token_store, token)
            logger.debug("Writing token to datastore")
            return token
        else:
            print("Unable to register device. server rejected request.")
    else:
        print("Missing optional registration key")
        print("Please set the REG_KEY environment variable to auto register device.")

    logger.info("Device registration unavailable. Missing required registration key")
    print("Unable to proceed, missing required TOKEN.")
    print("Please set the TOKEN environment variable")
    sys.exit(0)


def revoke_token():
    """Remove token form datastore if exists."""
    logger.info("Removing stored token if exists")
    token_store.unlink(missing_ok=True)
