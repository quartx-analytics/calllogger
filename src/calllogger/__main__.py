# Standard Lib
from queue import Queue
import argparse
import logging
import sys

# Third Party
import sentry_sdk

# Local
from calllogger.datastore import get_token
from calllogger.utils import TokenAuth
from calllogger.conf import settings
from calllogger.plugins import installed
from calllogger import __version__, running, api

logger = logging.getLogger(__name__)

# Parse command line args. Only used for version right now.
parser = argparse.ArgumentParser(prog="Quartx CallLogger")
parser.add_argument('--version', action='version', version=f"calllogger {__version__}")
parser.parse_args()


def get_plugin(selected_plugin: str):
    """Return the selected plugin."""
    if plugin := installed.get(selected_plugin.lower()):
        return plugin
    elif installed:
        print("Specified plugin not found:", selected_plugin)
        print("Available plugins are:")
        for plugin in installed.values():
            print(f"--> {plugin.__name__} - {plugin.__doc__}")
    else:
        print("No plugins are installed")

    # We only get here if the selected
    # plugin was not found
    sys.exit()


def set_sentry_user(token_auth: TokenAuth):
    """Request CDR user info and remap name to username for sentry support."""
    user_info = api.get_owner_info(token_auth)
    user_info["username"] = user_info.pop("name")
    sentry_sdk.set_user(user_info)


def main_loop(*args, **kwargs):
    try:
        return _main_loop(*args, **kwargs)
    except KeyboardInterrupt:
        # This will allow the threads
        # to gracefully shutdown
        running.clear()
        return 130


def _main_loop(plugin) -> int:
    running.set()
    token = get_token()
    tokenauth = TokenAuth(token)
    queue = Queue(settings.queue_size)

    # Configure sentry
    sentry_sdk.set_tag("plugin", plugin.__name__)
    set_sentry_user(tokenauth)

    # Start the CDR worker to monitor the record queue
    cdr_thread = api.CDRWorker(queue, tokenauth)
    cdr_thread.start()

    # Start the plugin thread to monitor for call records
    logger.info("Selected Plugin: %s - %s", plugin.__name__, plugin.__doc__)
    plugin_thread = plugin(_queue=queue)
    plugin_thread.start()

    # Sinse both threads share the same running event
    # If one dies, so should the other.
    cdr_thread.join()
    plugin_thread.join()
    return 0


# Entrypoint: calllogger
def monitor() -> int:
    """Normal logger that calls the users preferred plugin."""
    plugin = get_plugin(settings.plugin)
    return main_loop(plugin)


# Entrypoint: calllogger-mock
def mockcalls() -> int:
    """Force use of the mock logger."""
    plugin = get_plugin("MockCalls")
    return main_loop(plugin)


# Entrypoint: calllogger-getid
def getid() -> int:
    print(f"Device Identifier: {settings.identifier}")
    return 0


if __name__ == "__main__":
    # Normally this program will be called from an entrypoint
    # So we will force use of the mock plugin when called directly
    exit_code = mockcalls()
    sys.exit(exit_code)
