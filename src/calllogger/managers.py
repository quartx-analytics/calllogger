# Standard Lib
import threading
import time
import os

# Third Party
from sentry_sdk import capture_exception
from uptime import uptime
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
        # We get the process here as we should still be in the main thread
        # We do not get the right pid if running in a thread
        self.process = psutil.Process(os.getpid())

    def run(self):
        # We will sleep by 58 seconds instead of the desired 60
        # This is because each cpu_percent command will take 1 second to complete
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
            uptime=uptime(),
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
        process_uptime = time.time() - self.process.create_time()
        cpu_percent = min(100, self.process.cpu_percent(interval=1))

        # Use influx fields to store the values
        metrics.process_stats(fields=dict(
            uptime=process_uptime,
            cpu_percent=cpu_percent,
            ram_uss=self.process.memory_full_info().uss,
            ram_rss=self.process.memory_full_info().rss,
        )).write()
