# Standard Lib
import threading
import time

# Third Party
import pytest
import serial

# Local
from calllogger import CallDataRecord
from calllogger.plugins import SerialPlugin


# noinspection PyAbstractClass
class TestSerial(SerialPlugin):
    def __init__(self):
        super(TestSerial, self).__init__()
        self._running = running = threading.Event()
        running.set()

    @property
    def is_running(self):
        if hasattr(self, "__is_running__"):
            return False
        else:
            setattr(self, "__is_running__", True)
            return True


@pytest.fixture
def mock_serial(mocker):
    """Mock the serial lib Serial object to control return values."""
    mocked = mocker.patch.object(serial, "Serial", spec=True)
    mocker.patch.object(time, "sleep")

    def open_on_request():
        mocker.return_value.is_open = True

    # By default the serial interface will be closed until open is called
    mocked.return_value.open.side_effect = open_on_request
    mocked.return_value.is_open = False
    yield mocked


def test_open_serial_exception(mock_serial):
    class Test(TestSerial):
        def parse(self, validated_line: str) -> CallDataRecord:
            pass

    mock_serial.return_value.open.side_effect = serial.SerialException
    ret = Test()
    ret.run()

    assert mock_serial.return_value.is_open is False
