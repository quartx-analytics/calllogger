# Standard Lib
from queue import Queue
import pkg_resources
import threading
import sys

# Third Party
from sentry_sdk import configure_scope

# Local
from calllogger.conf import settings, TokenAuth
from calllogger.services.cdr import CDRWorker


def get_plugin():
    # Installed Plugin Entrypoints
    installed_plugins = {plugin.get_class().__name__.lower(): plugin for plugin in
                         pkg_resources.iter_entry_points("calllogger.plugin")}

    # Select plugin
    selected_plugin = settings.plugin.lower()
    if selected_plugin in installed_plugins:
        return installed_plugins[selected_plugin].get_class()
    elif installed_plugins:
        print("Specified plugin not found:", settings.plugin)
        print("Available plugins are:")
        for plugin in installed_plugins.values():
            print("-->", plugin.get_class().__name__)
    else:
        print("No plugins are installed")

    # Ws only get here if the selected
    # plugin was not found
    sys.exit()


def main_logger():
    queue = Queue(settings.queue_size)
    running = threading.Event()
    running.set()

    # Configure the sentry user
    with configure_scope() as scope:
        # noinspection PyDunderSlots, PyUnresolvedReferences
        scope.user = {"id": settings.token}

    # Start the plugin thread to monitor for call records
    plugin = get_plugin()
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


if __name__ == "__main__":
    main_logger()
