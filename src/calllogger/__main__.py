# Standard Lib
from queue import Queue
import functools
import argparse
import logging
import signal
import sys

# Third Party
import sentry_sdk

# Local
from calllogger.plugins import get_plugin
from calllogger import __version__, running, api, settings, metrics
from calllogger.managers import ThreadExceptionManager, SystemMetrics
from calllogger.auth import get_token

logger = logging.getLogger("calllogger")
# Parse command line args. Only used for version right now.
parser = argparse.ArgumentParser(prog="Quartx CallLogger")
parser.add_argument('--version', action='version', version=f"calllogger {__version__}")
parser.parse_known_args()


def terminate(signum, *_) -> int:
    """This will allow the threads to gracefully shutdown."""
    code = 143 if signum == signal.SIGTERM else 130
    metrics.collector.close()  # Flush metrics buffer
    running.clear()
    return code


def graceful_exception(func):
    """
    Decorator function to handle exceptions gracefully.
    And signal any threads to end.
    """
    @functools.wraps(func)
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


def main_loop(plugin: str) -> int:
    """Call the selected plugin and wait for program shutdown."""
    running.set()
    tokenauth = get_token()
    queue = Queue(settings.queue_size)
    client_info = api.get_client_info(tokenauth, settings.identifier)

    # Enable metrics reporting
    if settings.send_metrics and client_info["influxdb_token"]:
        metrics.collector.connect(
            token=client_info["influxdb_token"],
            identifier=settings.identifier,
            client=client_info["slug"],
        )

        # Monitor system stats
        stats_thread = SystemMetrics(daemon=True)
        stats_thread.start()

    # Configure sentry
    plugin = get_plugin(plugin if plugin else client_info["plugin"])
    sentry_sdk.set_tag("plugin", plugin.__name__)
    set_sentry_user(client_info)

    # Start the CDR worker to monitor the record queue
    cdr_thread = api.CDRWorker(queue, tokenauth)
    cdr_thread.start()

    # Start the plugin thread to monitor for call records
    plugin_thread = plugin(_queue=queue)
    plugin_thread.start()

    # Sinse both threads share the same running event
    # If one dies, so should the other.
    cdr_thread.join()
    plugin_thread.join()
    metrics.collector.close()  # Flush metrics buffer
    return ThreadExceptionManager.exit_code.value()


# Entrypoint: calllogger
@graceful_exception
def monitor() -> int:
    """Normal logger that calls the users preferred plugin."""
    return main_loop(settings.plugin)


# Entrypoint: calllogger-mock
@graceful_exception
def mockcalls() -> int:
    """Force use of the mock logger."""
    return main_loop("MockCalls")


# Entrypoint: calllogger-getid
@graceful_exception
def getid() -> int:
    identifier = settings.identifier
    print(identifier)
    return 0


# Gracefully shutdown for 'kill <pid>' or docker stop <container>
signal.signal(signal.SIGTERM, terminate)

if __name__ == "__main__":
    # Normally this program will be called from an entrypoint
    # So we will force use of the mock plugin when called directly
    exit_code = mockcalls()
    sys.exit(exit_code)
