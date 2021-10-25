# Standard Lib
import threading
import functools
import signal

# Third Party
from sentry_sdk import capture_exception

# Local
from calllogger.utils import ExitCodeManager
from calllogger import closeers, stopped


class ThreadTimer(threading.Thread):
    """
    Call a function after a specified number of seconds.

    :param float or int interval: The time to wait for before executing the function.
    :param callable function: The function to call.
    :param args: The position args to send to the function.
    :param kwargs: The keyword args to send to the function.
    :param bool repeat: When set to True, the thread will repeatedly call the function
    """

    def __init__(self, interval, function, args=None, kwargs=None, repeat=False):
        super(ThreadTimer, self).__init__()
        self.interval = interval
        self.function = function
        self.repeat = repeat
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}

    def run(self):
        # Run the function after waiting
        # if program has not stopped
        while not stopped.wait(self.interval):
            self.function(*self.args, **self.kwargs)

            # Keep looping if repeat is True, quit otherwise
            if self.repeat:
                continue
            else:
                break


class ThreadExceptionManager(threading.Thread):
    exit_code = ExitCodeManager()

    def run(self) -> bool:
        try:
            self.entrypoint()
        except Exception as err:
            capture_exception(err)
            self.exit_code.set(1)
            return False
        except SystemExit as err:
            self.exit_code.set(err.code)
            return True
        else:
            return True
        finally:
            stopped.set()

    def entrypoint(self):  # pragma: no cover
        raise NotImplementedError


# noinspection PyBroadException
def terminate(signum, *_) -> int:
    """This will allow the threads to gracefully shutdown."""
    # Close registered closers
    for callable_func in closeers:
        try:
            callable_func()
        except Exception:
            pass

    code = 143 if signum == signal.SIGTERM else 130
    stopped.set()
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
            stopped.set()
    return wrapper
