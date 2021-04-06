# Standard Lib
from queue import Queue
import threading
import argparse
import sys

# Third Party
from sentry_sdk import configure_scope

# Local
from calllogger.conf import settings, TokenAuth
from calllogger.api.cdr import CDRWorker
from calllogger.plugins import installed
from calllogger import __version__

# Parse command line args. Only used for version right now.
parser = argparse.ArgumentParser(prog="Quartx CallLogger")
parser.add_argument('--version', action='version', version=f"calllogger {__version__}")
parser.parse_args()


def get_plugin(selected_plugin: str):
    selected_plugin = selected_plugin.lower()

    # Select plugin
    if selected_plugin in installed:
        return installed[selected_plugin]
    elif installed:
        print("Specified plugin not found:", settings.plugin)
        print("Available plugins are:")
        for plugin in installed.values():
            print(f"--> {plugin.__name__}: {plugin.__doc__}", )
    else:
        print("No plugins are installed")

    # Ws only get here if the selected
    # plugin was not found
    sys.exit()


def main_logger(plugin) -> int:
    queue = Queue(settings.queue_size)
    running = threading.Event()
    running.set()

    # Configure the sentry user
    with configure_scope() as scope:
        # noinspection PyDunderSlots, PyUnresolvedReferences
        scope.user = {"id": settings.token}

    # Start the plugin thread to monitor for call records
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


def main() -> int:
    """Normal logger that calls the users preferred plugin."""
    plugin = get_plugin(settings.plugin)
    return main_logger(plugin)


def mocker() -> int:
    """Force use of the mock logger."""
    plugin = get_plugin("MockCalls")
    return main_logger(plugin)


if __name__ == "__main__":
    # Normally this program will be called from a entrypoint.
    # So we will use the mock plugin here when directly called.
    exit_code = mocker()
    sys.exit(exit_code)
