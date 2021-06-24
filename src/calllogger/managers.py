# Standard Lib
import threading

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

    def run(self):
        # We will sleep by 59 seconds instead of the desired 60
        # This is because the cpu_percent command will take 1 second to complete
        while sleeper(1, running.is_set):
            self.gather_metrics()

    # noinspection PyMethodMayBeStatic
    def gather_metrics(self):
        # Extract system stats
        disk = psutil.disk_usage("/")
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu_percent = min(100, psutil.cpu_percent())#interval=1))

        # Use influx fields to store the values
        metrics.system_stats.fields(
            disk_used=disk.used,
            disk_total=disk.total,
            ram_used=ram.used,
            ram_total=ram.total,
            swap_used=swap.used,
            swap_total=swap.total,
            cpu_percent=cpu_percent,
        ).write()
