# Standard Lib
import logging

# Third Party
import os

import pytest
from pytest_mock import MockerFixture

# Local
from calllogger import utils


@pytest.mark.parametrize("level, expected", [
    (logging.DEBUG, True),
    (logging.INFO, True),
    (logging.WARNING, False),
    (logging.ERROR, False),
    (logging.CRITICAL, False),
])
def test_only_messages(level, expected):
    """Test that the filter returns false for log messages of Warning or greater."""
    logfilter = utils.OnlyMessages("testlogger")
    # noinspection PyTypeChecker
    value = logfilter.filter(logging.LogRecord("testlogger", level, "", 1, None, tuple(), {"test": None}))
    assert value is expected


def test_timeout_decay(mocker: MockerFixture):
    class Settings:
        timeout = 3
        max_timeout = 300
        timeout_decay = 1.5

    # Test that timeout decay is working
    mocked = mocker.patch("time.sleep")
    timeout = utils.Timeout(Settings, lambda: True)
    assert timeout.value == 3
    for i in [4, 6, 9, 13, 19, 28, 42, 63, 94, 141, 211, 300, 300, 300]:
        timeout.sleep()
        mocked.assert_called()
        assert timeout.value == i
        mocked.reset_mock()

    # Test the reset works as exspected
    timeout.reset()
    assert timeout.value == 3


def test_sleeper(disable_sleep):
    """Test that time.sleep gets called twice as much as the timeout."""
    utils.sleeper(5, lambda: True)
    assert disable_sleep.call_count == 10


@pytest.mark.parametrize("env_string", [
    "testdata",
    "ZW5jb2RlZDo=dGVzdGRhdGE=",
])
def test_base64_decoder(env_string, mock_env):
    mock_env("dummy_env", env_string)
    value = utils.decode_env("dummy_env")
    assert value == "testdata"


class TestExitCodeManager:
    def test_dups_ignored(self):
        """Test that exit code can't be changed once set."""
        exit_code = utils.ExitCodeManager()

        # Exit code should be set to 22
        exit_code.set(22)
        assert exit_code.value() == 22

        # Exit code should be ignored and say at 22
        exit_code.set(11)
        assert exit_code.value() == 22

    def test_reset(self):
        """Test that exit code can be reset."""
        exit_code = utils.ExitCodeManager()

        # Exit code should be set to 22
        exit_code.set(22)
        assert exit_code.value() == 22

        # Reset should allow the code to be changed again
        exit_code.reset()
        exit_code.set(11)
        assert exit_code.value() == 11
