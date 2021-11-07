# Standard Lib
import logging
import threading
import functools
import signal

# Third Party
from sentry_sdk import push_scope, capture_exception

# Local
from calllogger import closeers, stopped

logger = logging.getLogger("calllogger")


class ThreadTimer(threading.Thread):
    """
    Call a function after a specified number of seconds.

    :param float or int interval: The time to wait before executing the function.
    :param callable function: The function to call.
    :param args: The position args to send to the function.
    :param kwargs: The keyword args to send to the function.
    :param bool repeat: When set to True, the thread will repeatedly call the function
    :param bool quit_on_exc: Flag if set will cause the timer to quit when an exception is raised inside function.
    """

    def __init__(self, interval, function, args=None, kwargs=None, repeat=False, quit_on_exc=False):
        super(ThreadTimer, self).__init__()
        self.interval = interval
        self.function = function
        self.repeat = repeat
        self.quit_on_exc = quit_on_exc
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}

    def run(self):
        # Run the function after waiting
        # if program has not stopped
        while not stopped.wait(self.interval):
            with push_scope() as scope:
                try:
                    self.function(*self.args, **self.kwargs)
                except Exception as err:
                    capture_exception(err, scope=scope)
                    if self.quit_on_exc:
                        break

            # Keep looping if repeat is True, quit otherwise
            if self.repeat:  # pragma: no branch
                continue
            else:
                break  # pragma: no cover


class ThreadExceptionManager(threading.Thread):
    """
    Same as a normal threading.Thread but with
    Exception handling for the run method.
    """

    def run(self) -> bool:
        try:
            self.entrypoint()
        except Exception as err:
            capture_exception(err)
            logger.warning(err)
            stopped.set(1)
            return False
        except SystemExit as err:
            stopped.set(err.code)
            return True
        else:
            stopped.set()
            return True

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
    stopped.set(code)
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
