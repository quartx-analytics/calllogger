# Standard Lib
from pathlib import PosixPath
import logging
import base64

# Third Party
import pytest
from pytest_mock import MockerFixture

# Local
from calllogger import utils, stopped


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
    mocked = mocker.patch.object(stopped, "wait")
    timeout = utils.Timeout(Settings, stopped)
    values = [3, 4, 6, 9, 13, 19, 28, 42, 63, 94, 141, 211, 300, 300, 300]
    for count, i in enumerate(values[1:]):
        assert timeout.value == values[count]
        timeout.sleep()
        mocked.assert_called_with(values[count])
        assert timeout.value == i
        mocked.reset_mock()

    # Test that value assignment get reset after sleeping
    assert timeout.value == 300
    timeout.value = 500
    assert timeout.value == 500  # Should now be the new value
    timeout.sleep()
    mocked.assert_called_with(500)
    assert timeout.value == 300  # Should be original value

    # Test the reset works as exspected
    timeout.reset()
    assert timeout.value == 3


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
