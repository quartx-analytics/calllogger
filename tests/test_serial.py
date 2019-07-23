from unittest import mock
import pytest
import serial

# Package
from call_logger.plugins.siemens_hipath_serial import SiemensHipathSerial
from call_logger.record import Record
from call_logger import api

mock_data = b"""
10.04.1923:19:06  2   104     00:00:0500441619251900                       2
10.04.1923:28:01  2      00:0100:00:000061393038625                        2
10.04.1923:28:01  2      00:0100:00:000061393038625                        2
10.04.1923:28:01  2      00:0100:00:000061393038625                        2
10.04.1923:19:06  2   104     00:00:0500441619251900                       2
11.04.1900:33:20  1   104     00:00:020857739075                           9
11.04.1900:34:13  2   104     00:00:060876153281                           2
11.04.1900:35:38  1   104             0876153281                           0
11.04.1900:35:38  1   103             0876153281                           0
11.04.1900:35:48  1   10400:0100:00:070876153281                           1
11.04.1900:36:28  2   104             79923                                0
11.04.1900:36:29  2   103             79923                                0
11.04.1900:36:34  2   10000:0500:00:0079923                                1
11.04.1900:49:13  1   104             0876153281                           0
11.04.1900:49:13  1   103             0876153281                           0
11.04.1900:49:22  2   104     00:00:030857739075                           2
11.04.1900:49:24  1   10000:1000:00:000876153281                           1
09.09.1821:04:01  1   100             0811111111                           0 9923
09.09.1820:16:50  1   10000:0100:00:060877629926                           1 9923
02.09.1814:07:40  1   10000:0900:00:000877629926                           2
22.02.1923:11:41  3   048             0248873711                           0 4416
22.02.1923:11:43  3   04800:4100:10:030248873711                           1 4416
22.02.1922:55:27  3   05800:0700:00:000922735086                           2
11.04.1914:58:19  1   103                                                  0
""".strip().split(b"\n")


@pytest.fixture
def mock_api():
    with mock.patch.object(api, "API") as mocker:
        mocker.return_value.running.return_value.is_set.return_value = True
        yield mocker


@pytest.fixture
def mock_serial():
    with mock.patch.object(serial, "Serial", spec=True) as mocker:
        def open_on_request():
            mocker.return_value.is_open = True
        mocker.return_value.open.side_effect = open_on_request
        mocker.return_value.is_open = False
        yield mocker


@pytest.fixture(params=mock_data)
def serial_params(request, mock_serial):
    mock_serial.return_value.readline.side_effect = [request.param, KeyboardInterrupt]
    return mock_serial


def test_call_logs(mock_api, serial_params):
    """Test the serial parser with different lines of call data."""
    def push(record):
        # Check if we have a Record class
        assert isinstance(record, Record)

        # The expected values for a given call type
        required_fields = ["number", "ext", "line"]
        if record.call_type == record.OUTGOING or record.call_type == record.RECEIVED:
            required_fields.extend(["ring", "duration"])

        # Check if the required fields exists
        for val in required_fields:
            assert val in record

    mock_api.return_value.push.side_effect = push
    plugin = SiemensHipathSerial("/dev/ttyUSB0", 9600)
    plugin.start()


def test_failed_connection(mock_api, mock_serial):
    """Check that the SerialException is caught."""
    mock_serial.return_value.open.side_effect = [serial.SerialException, KeyboardInterrupt]
    plugin = SiemensHipathSerial("/dev/ttyUSB0", 9600, timeout=0.01)
    plugin.start()

    mock_serial.return_value.open.assert_called()


def test_read_handled_exception(mock_api, mock_serial):
    mock_serial.return_value.readline.side_effect = [serial.SerialException, KeyboardInterrupt]
    plugin = SiemensHipathSerial("/dev/ttyUSB0", 9600, timeout=0.01)
    plugin.start()

    mock_serial.return_value.readline.assert_called()


def test_read_unhandled_exception(mock_api, mock_serial):
    mock_serial.return_value.readline.side_effect = RuntimeError
    plugin = SiemensHipathSerial("/dev/ttyUSB0", 9600, timeout=0.01)
    with pytest.raises(RuntimeError):
        plugin.start()


def test_parse_error(mock_api, mock_serial):
    mock_serial.return_value.readline.side_effect = [b"dkdi", KeyboardInterrupt]
    plugin = SiemensHipathSerial("/dev/ttyUSB0", 9600, timeout=0.01)
    plugin.parse = mock.Mock(side_effect=RuntimeError)
    plugin.start()

    mock_serial.return_value.readline.assert_called()
