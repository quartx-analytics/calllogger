# Standard Lib
import signal

# Third Party
import pytest
from pytest_mock import MockerFixture

# Local
from calllogger import misc
from calllogger import running


class TestThreadExceptionManager:
    def test_success(self, mocker):
        """
        Test that a successful call to entrypoint
        causes no errors and returns True
        """
        spy_running_clear = mocker.spy(running, "clear")
        misc.ThreadExceptionManager.exit_code.reset()

        class Success(misc.ThreadExceptionManager):
            def entrypoint(self):
                return None

        manager = Success().run()
        assert manager is True
        assert spy_running_clear.called

    def test_system_exit(self, mocker):
        """
        Test that run catches the SystemExit exception
        and that the code is captured too.
        """
        spy_running_clear = mocker.spy(running, "clear")
        misc.ThreadExceptionManager.exit_code.reset()

        class Success(misc.ThreadExceptionManager):
            def entrypoint(self):
                raise SystemExit(22)

        manager = Success().run()
        assert manager is True
        assert spy_running_clear.called
        assert Success.exit_code.value() == 22

    @pytest.mark.parametrize("exc", [RuntimeError, KeyError, ValueError])
    def test_exception(self, mocker, exc):
        """
        Test that run catches the SystemExit exception
        and that the code is captured too.
        """
        spy_running_clear = mocker.spy(running, "clear")
        misc.ThreadExceptionManager.exit_code.reset()

        class Success(misc.ThreadExceptionManager):
            def entrypoint(self):
                raise exc()

        manager = Success().run()
        assert manager is False
        assert spy_running_clear.called
        assert Success.exit_code.value() == 1


@pytest.mark.parametrize("return_data", [KeyboardInterrupt, "testdata"])
def test_graceful_exception(mocker: MockerFixture, return_data):
    spy_running_clear = mocker.spy(running, "clear")
    spy_terminate = mocker.spy(misc, "terminate")

    @misc.graceful_exception
    def worker():
        if isinstance(return_data, str):
            return return_data
        else:
            raise KeyboardInterrupt

    worker()
    assert spy_running_clear.called
    if isinstance(return_data, Exception):
        spy_terminate.assert_called_with(signal.SIGINT)
