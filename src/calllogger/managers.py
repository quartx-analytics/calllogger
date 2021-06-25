# Standard Lib
import threading
import os

# Third Party
from sentry_sdk import capture_exception
import psutil

# Local
from calllogger.utils import ExitCodeManager, sleeper
from calllogger import running, metrics


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
            running.clear()

    def entrypoint(self):  # pragma: no cover
        raise NotImplementedError


class SystemMetrics(threading.Thread):
    """Monitor the system metrics like CPU usage, Memory usage, disk usage and swap usage."""

    def __init__(self, *args, **kwargs):
        super(SystemMetrics, self).__init__(*args, **kwargs)
        # We get the pid here as we should still be in the main thread
        # We do not get the right pid if running in a thread
        self.pid = os.getpid()

    def run(self):
        # We will sleep by 58 seconds instead of the desired 60
        # This is because the cpu_percent command will take 1 second to complete
        while sleeper(58, running.is_set):
            self.gather_system_metrics()
            self.gather_process_metrics()

    # noinspection PyMethodMayBeStatic
    def gather_system_metrics(self):
        # Extract system stats
        disk = psutil.disk_usage("/")
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu_percent = min(100, psutil.cpu_percent(interval=1))

        # Use influx fields to store the values
        metrics.system_stats(fields=dict(
            disk_used=disk.used,
            disk_total=disk.total,
            ram_used=ram.used,
            ram_total=ram.total,
            swap_used=swap.used,
            swap_total=swap.total,
            cpu_percent=cpu_percent,
        )).write()

    # noinspection PyMethodMayBeStatic
    def gather_process_metrics(self):
        process = psutil.Process(self.pid)

        # Use influx fields to store the values
        metrics.process_stats(fields=dict(
            ram_uss=process.memory_full_info().uss,
            ram_rss=process.memory_full_info().rss,
            cpu_percent=min(100, process.cpu_percent(interval=1)),
        )).write()
