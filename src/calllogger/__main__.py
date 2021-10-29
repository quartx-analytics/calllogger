# Standard Lib
from queue import SimpleQueue
import argparse
import logging
import signal
import sys

# Third Party
import sentry_sdk

# Local
from calllogger.plugins import get_plugin
from calllogger import __version__, api, settings, stopped, telemetry
from calllogger.auth import get_token
from calllogger.misc import graceful_exception, terminate

logger = logging.getLogger("calllogger")

# Parse command line args. Only used for version right now.
parser = argparse.ArgumentParser(prog="Quartx CallLogger")
parser.add_argument('--version', action='version', version=f"calllogger {__version__}")
parser.parse_known_args()


def initialise_telemetry(client_info: dict):
    """Collect system metrics and logs."""
    # Enable metrics telemetry
    if settings.collect_metrics and client_info["influx_token"]:
        api.InfluxWrite(
            url=client_info["influx_url"],
            collector=telemetry.collector,
            token=client_info["influx_token"],
            default_fields=dict(
                identifier=settings.identifier,
                client=client_info["slug"],
            )
        ).start()

    # Enable logs telemetry
    if settings.collect_logs:
        telemetry.send_logs_to_logzio(
            client_info=client_info,
        )


def main_loop(plugin: str) -> int:
    """Call the selected plugin and wait for program shutdown."""
    tokenauth = get_token()
    client_info = api.get_client_info(tokenauth, settings.identifier)

    # Initialise telemetry if we are able to
    initialise_telemetry(client_info)

    # Enable periodic checkin
    api.setup_client_checkin(tokenauth, settings.identifier)

    # Configure sentry
    plugin = get_plugin(plugin if plugin else client_info["settings"]["plugin"])
    sentry_sdk.set_tag("plugin", plugin.__name__)

    # Start the CDR worker to monitor the record queue
    queue = SimpleQueue()
    cdr_thread = api.CDRWorker(queue, tokenauth)
    cdr_thread.start()

    # Start the plugin thread to monitor for call records
    plugin_thread = plugin(_queue=queue)
    plugin_thread.start()

    # Block untill the stop event has been triggered
    stopped.wait()
    return stopped.get_exit_code()


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
