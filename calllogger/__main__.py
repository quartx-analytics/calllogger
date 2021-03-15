# Standard Lib
import pkg_resources

# Local
import calllogger


def main():


# Installed Plugin EntryPoints
# https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entrypoint-objects
INSTALLED_PLUGINS = {plugin.name: plugin for plugin in pkg_resources.iter_entry_points("calllogger.plugin")}

# Setup buffer queue
self._queue = queue.Queue(settings.QUEUE_SIZE)

# Running Flag, Indecates that the API is still working
self._running = threading.Event()
self._running.set()

# Start the API thread to monitor for call records and send them to server
self._api_thread = api.API(self._queue, self._running)
self._api_thread.start()

try:
    self.run()
except KeyboardInterrupt:
    self.logger.debug("Keyboard Interrupt accepted.")
finally:
    self._running.clear()

if __name__ == "__main__":
    pass
