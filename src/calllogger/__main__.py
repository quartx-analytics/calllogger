# Standard Lib
from queue import Queue
import argparse
import logging
import signal
import sys

# Third Party
import sentry_sdk

# Local
from calllogger.plugins import get_plugin
from calllogger import __version__, running, api, settings
from calllogger.datastore import get_token, get_identifier
from calllogger.managers import ThreadExceptionManager

logger = logging.getLogger(__name__)

# Parse command line args. Only used for version right now.
parser = argparse.ArgumentParser(prog="Quartx CallLogger")
parser.add_argument('--version', action='version', version=f"calllogger {__version__}")
parser.parse_known_args()


def terminate(signum, *_):
    """This will allow the threads to gracefully shutdown."""
    code = 143 if signum == signal.SIGTERM else 130
    running.clear()
    return code


def graceful_exception(func):
    """
    Decorator function to handle exceptions gracefully.
    And signal any threads to end.
    """
    def wrapper(*args, **kwargs) -> int:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            return terminate(signal.SIGINT)
        finally:
            running.clear()
    return wrapper


def set_sentry_user(client_info: dict):
    """Setup sentry user using client info."""
    sentry_sdk.set_user({
        "id": client_info["id"],
        "username": client_info["name"],
        "email": client_info["email"],
    })


def main_loop(plugin) -> int:
    """Call the selected plugin and wait for program shutdown."""
    running.set()
    tokenauth = get_token()
    queue = Queue(settings.queue_size)

    # Configure sentry
    sentry_sdk.set_tag("plugin", plugin.__name__)
    client_info = api.get_owner_info(tokenauth)
    set_sentry_user(client_info)

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
    return ThreadExceptionManager.exit_code.value()


# Entrypoint: calllogger
@graceful_exception
def monitor() -> int:
    """Normal logger that calls the users preferred plugin."""
    plugin = get_plugin(settings.plugin)
    return main_loop(plugin)


# Entrypoint: calllogger-mock
@graceful_exception
def mockcalls() -> int:
    """Force use of the mock logger."""
    plugin = get_plugin("MockCalls")
    return main_loop(plugin)


# Entrypoint: calllogger-getid
@graceful_exception
def getid() -> int:
    identifier = get_identifier()
    print(identifier)
    return 0


# Gracefully shutdown for 'kill <pid>' or docker stop <container>
signal.signal(signal.SIGTERM, terminate)

if __name__ == "__main__":
    # Normally this program will be called from an entrypoint
    # So we will force use of the mock plugin when called directly
    exit_code = mockcalls()
    sys.exit(exit_code)
