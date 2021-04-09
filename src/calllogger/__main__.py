# Standard Lib
from queue import Queue
import threading
import argparse
import logging
import sys

# Third Party
import sentry_sdk

# Local
from calllogger.conf import settings, TokenAuth
from calllogger.api.cdr import CDRWorker
from calllogger.api.info import get_owner_info
from calllogger.plugins import installed
from calllogger import __version__

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


def main_loop(plugin) -> int:
    queue = Queue(settings.queue_size)
    running = threading.Event()
    running.set()

    # Configure sentry
    sentry_sdk.set_tag("plugin", plugin.__name__)
    sentry_sdk.set_user(get_owner_info())

    # Start the plugin thread to monitor for call records
    logger.info("Selected Plugin: %s - %s", plugin.__name__, plugin.__doc__)
    plugin_thread = plugin(_queue=queue, _running=running)
    plugin_thread.start()

    # Start the CDR worker to monitor the record queue
    token_auth = TokenAuth(settings.token)
    cdr_thread = CDRWorker(queue, running, token_auth)
    cdr_thread.start()

    # Sinse both threads have the same running event
    # If one dies, so should the other.
    try:
        plugin_thread.join()
        cdr_thread.join()
    except KeyboardInterrupt:
        # This will allow the threads
        # to gracefully shutdown
        running.clear()
        return 130


def monitor() -> int:
    """Normal logger that calls the users preferred plugin."""
    plugin = get_plugin(settings.plugin)
    return main_loop(plugin)


def mocker() -> int:
    """Force use of the mock logger."""
    plugin = get_plugin("MockCalls")
    return main_loop(plugin)


if __name__ == "__main__":
    # Normally this program will be called from an entrypoint
    # So we will force use of the mock plugin when directly called
    exit_code = mocker()
    sys.exit(exit_code)
