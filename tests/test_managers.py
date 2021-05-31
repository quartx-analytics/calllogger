# Third Party
import pytest

# Local
from calllogger.managers import ThreadExceptionManager
from calllogger import running


def test_success(mocker):
    """
    Test that a successful call to entrypoint
    causes no errors and returns True
    """
    spy_running_clear = mocker.spy(running, "clear")

    class Success(ThreadExceptionManager):
        def entrypoint(self):
            return None

    manager = Success().run()
    assert manager is True
    assert spy_running_clear.called


def test_system_exit(mocker):
    """
    Test that run catches the SystemExit exception
    and that the code is captured too.
    """
    spy_running_clear = mocker.spy(running, "clear")

    class Success(ThreadExceptionManager):
        def entrypoint(self):
            raise SystemExit(22)

    manager = Success().run()
    assert manager is True
    assert spy_running_clear.called
    assert Success.exit_code.value() == 22


@pytest.mark.parametrize("exc", [RuntimeError, KeyError, ValueError])
def test_exception(mocker, exc):
    """
    Test that run catches the SystemExit exception
    and that the code is captured too.
    """
    spy_running_clear = mocker.spy(running, "clear")

    class Success(ThreadExceptionManager):
        def entrypoint(self):
            raise exc()

    manager = Success().run()
    assert manager is False
    assert spy_running_clear.called
    assert Success.exit_code.value() == 1
