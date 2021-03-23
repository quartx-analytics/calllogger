# Standard Lib
import logging

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

    class Thread:
        is_running = True

    # Test that timeout decay is working
    mocked = mocker.patch("time.sleep")
    timeout = utils.Timeout(Settings, Thread)
    assert timeout.value == 3
    for i in [4, 6, 9, 13, 19, 28, 42, 63, 94, 141, 211, 300, 300, 300]:
        timeout.sleep()
        mocked.assert_called()
        assert timeout.value == i
        mocked.reset_mock()

    # Test the reset works as exspected
    timeout.reset()
    assert timeout.value == 3
