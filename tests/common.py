# Standard Lib
import queue


def call_plugin(plugin):
    """Call plugin with required parameters."""
    call_queue = queue.SimpleQueue()
    return plugin(_queue=call_queue)
