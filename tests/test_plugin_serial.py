# Standard Lib
import threading
import time

# Third Party
import pytest
import serial

# Local
from calllogger.plugins import SerialPlugin


# noinspection PyAbstractClass
class TestPlugin(SerialPlugin):
    def __init__(self):
        super().__init__()
        self._running = running = threading.Event()
        running.set()

    def parse(self, validated_line):
        pass


@pytest.fixture
def mock_serial(mocker):
    """Mock the serial lib Serial object to control return values."""
    mocked = mocker.patch.object(serial, "Serial", spec=True)

    def open_on_request():
        mocked.return_value.configure_mock(is_open=True)

    def close_request():
        mocked.return_value.configure_mock(is_open=False)

    # By default the serial interface will be closed until open is called
    mocked.return_value.open.side_effect = open_on_request
    mocked.return_value.close.side_effect = close_request
    mocked.return_value.configure_mock(is_open=False)
    yield mocked.return_value


@pytest.fixture
def mock_plugin(mocker):
    plugin = TestPlugin()
    mocked_runner = mocker.patch.object(plugin, "_running")
    mocked_runner.is_set.side_effect = [True, False]
    mocker.patch.object(time, "sleep")
    yield plugin


def test_open_serial_exception(mock_serial, mock_plugin, mocker):
    mock_serial.open.side_effect = serial.SerialException
    timeout = mocker.spy(mock_plugin.timeout, "sleep")
    mock_plugin.run()

    assert timeout.called
    assert not mock_serial.is_open


def test_read_serial_line(mock_serial, mock_plugin):
    mock_serial.readline.side_effect = serial.SerialException
    mock_plugin.run()

    assert mock_serial.readline.called
    assert not mock_serial.is_open
    assert mock_serial.close.called
