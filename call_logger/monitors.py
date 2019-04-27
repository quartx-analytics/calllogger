# Standard library
import pkgutil

# Third party imports
import queue

# Package imports
from . import config, plugins, logger


class QueueManager(object):
    def __init__(self, limit=100):
        self.limit = limit
        self.queues = []

    def create(self):
        call_queue = queue.Queue(self.limit)
        self.queues.append(call_queue)
        return call_queue

    def put(self, record):
        if len(self.queues) == 1:
            self.queues[0].put(record)
        else:
            for call_queue in self.queues:
                try:
                    call_queue.put_nowait(record)
                except queue.Full as e:
                    logger.exception(e)


def monitor(*reporters: callable):
    """
    Monitor a phone system for incomming and outgoing calls, sending logs to a call monitoring frontend.
    At the moment only one system is supported, the Siemens Hipath phone system using the serail interface.
    """
    # The queue of call logs ready
    # to be send to the frontend
    queue_manager = QueueManager(100)

    # Start the Reporter that sends the call logs to the frontend
    for reporter in reporters:
        call_queue = queue_manager.create()
        frontend = reporter(call_queue)
        frontend.daemon = True
        frontend.start()

    # Select phone system parser
    phone_system = config["settings"]["phone_system"]
    load_plugins()

    try:
        # Load required plugin
        plugin = plugins.systems[phone_system.lower()]
    except KeyError:
        raise KeyError(f"unknown phone system: {phone_system}")
    else:
        # Initialize the plugin
        plugin(queue_manager)


def load_plugins():
    """Import all plugin's so they can be registered."""
    prefix = plugins.__name__ + "."
    for _, modname, _ in pkgutil.iter_modules(plugins.__path__, prefix):
        __import__(modname)
