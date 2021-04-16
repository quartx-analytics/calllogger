# Standard Lib
import threading
import queue


def call_plugin(plugin):
    """Call plugin with required parameters."""
    call_queue = queue.Queue()
    running = threading.Event()
    running.set()
    return plugin(_queue=call_queue, _running=running)
