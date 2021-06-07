# Standard Lib
from pathlib import PosixPath
import logging
import base64

# Third Party
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


class TestReadWrite:
    """Test read_datastore and write_datastore functions."""

    def test_read(self, mocker: MockerFixture):
        """Test that datastore reads and decodes correctly."""
        encoded_data = base64.b64encode(b"testdata")
        mocked_open = mocker.patch.object(PosixPath, "open", mocker.mock_open(read_data=encoded_data))

        path = PosixPath("/data")
        value = utils.read_datastore(path)

        mocked_open.assert_called_with("rb")
        assert mocked_open.return_value.read.called
        assert value == "testdata"

    def test_write(self, mocker: MockerFixture):
        """Test that datastore writes encoded data."""
        encoded_data = base64.b64encode(b"testdata")
        mocked_open = mocker.patch.object(PosixPath, "open", mocker.mock_open())

        path = PosixPath("/data")
        utils.write_datastore(path, "testdata")

        mocked_open.assert_called_with("wb")
        mocked_open.return_value.write.assert_called_with(encoded_data)
