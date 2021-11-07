# Standard Lib
from unittest.mock import Mock
import signal

# Third Party
import pytest
from pytest_mock import MockerFixture

# Local
from calllogger import misc, stopped, closeers


class TestThreadExceptionManager:
    def test_success(self, mocker):
        """
        Test that a successful call to entrypoint
        causes no errors and returns True
        """
        spy_running_clear = mocker.spy(stopped, "set")

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
        spy_running_clear = mocker.spy(stopped, "set")

        class Success(misc.ThreadExceptionManager):
            def entrypoint(self):
                raise SystemExit(22)

        manager = Success().run()
        assert manager is True
        assert spy_running_clear.called
        assert stopped.get_exit_code() == 22

    @pytest.mark.parametrize("exc", [RuntimeError, KeyError, ValueError])
    def test_exception(self, mocker, exc):
        """
        Test that run catches the SystemExit exception
        and that the code is captured too.
        """
        spy_running_clear = mocker.spy(stopped, "set")

        class Success(misc.ThreadExceptionManager):
            def entrypoint(self):
                raise exc()

        manager = Success().run()
        assert manager is False
        assert spy_running_clear.called
        assert stopped.get_exit_code() == 1


@pytest.mark.parametrize("return_data", [KeyboardInterrupt, "testdata"])
def test_graceful_exception(mocker: MockerFixture, return_data):
    spy_running_clear = mocker.spy(stopped, "set")
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


class Testterminate:
    def test_terminate(self):
        """Test that terminate set the stopped event flag."""
        misc.terminate(signal.SIGINT)
        assert stopped.is_set()

    @pytest.mark.parametrize("event,value", [(signal.SIGINT, 130), (signal.SIGTERM, 143)])
    def test_terminate_exit_code(self, event, value):
        """Test that terminate returns the right exit code for the right signal"""
        ret = misc.terminate(event)
        assert stopped.is_set()
        assert ret == value

    @pytest.mark.parametrize("error", [False, True])
    def test_terminate_call_close(self, error):
        """Test that terminate sets the stopped event flag."""
        closed = False

        def close():
            nonlocal closed
            closed = True
            if error:
                raise RuntimeError

        # Keep org to reset back later
        org_closers = closeers[:]
        closeers.append(close)

        misc.terminate(signal.SIGINT)
        assert stopped.is_set()
        assert closed

        # Reset back to org
        closeers.clear()
        closeers.extend(org_closers)


class TestThreadTimer:
    def test_basic_use(self, disable_sleep: Mock):
        """Test that the function gets called."""
        called = False

        def test_func(*_, **__):
            nonlocal called
            called = True

        interval = 10
        timer = misc.ThreadTimer(interval, test_func)
        timer.start()
        timer.join()

        disable_sleep.assert_called_once_with(interval)
        assert called is True

    def test_args_passed(self, disable_sleep: Mock):
        """Test that the function gets called with the right args."""
        called = False

        def test_func(test_arg, new=False):
            nonlocal called
            called = True
            assert test_arg == "passed"
            assert new is True

        interval = 10
        timer = misc.ThreadTimer(interval, test_func, args=["passed"], kwargs={"new": True})
        timer.start()
        timer.join()

        disable_sleep.assert_called_once_with(interval)
        assert called is True

    def test_repeater(self, disable_sleep: Mock):
        """Test that the function gets called repeatedly."""
        called = 0

        def test_func():
            nonlocal called
            called += 1

        interval = 10
        disable_sleep.side_effect = [False, False, True]
        timer = misc.ThreadTimer(interval, test_func, repeat=True)
        timer.start()
        timer.join()

        disable_sleep.assert_called_with(interval)
        assert called == 2

    def test_exception(self, disable_sleep: Mock):
        """Test that an exception within function don't pop up the stack."""
        called = False

        def test_func():
            nonlocal called
            called = True
            raise RuntimeError

        interval = 10
        timer = misc.ThreadTimer(interval, test_func)
        timer.start()
        timer.join()

        disable_sleep.assert_called_once_with(interval)
        assert called is True

    def test_exception_quit(self, disable_sleep: Mock):
        """Test that the timer quits when exception is raised, repeater stops."""
        called = 0

        def test_func():
            nonlocal called
            called += 1
            raise RuntimeError

        interval = 10
        disable_sleep.side_effect = [False, False, True]  # Should cause function to get call 2 times
        timer = misc.ThreadTimer(interval, test_func, repeat=True, quit_on_exc=True)
        timer.start()
        timer.join()

        disable_sleep.assert_called_with(interval)
        assert called == 1
