# Standard Lib
import time

# Third Party
import pytest
import serial

# Local
from calllogger.plugins import SerialPlugin
from calllogger.record import CallDataRecord
from ..common import call_plugin
from calllogger import running


# noinspection PyAbstractClass
class MockPlugin(SerialPlugin):
    def parse(self, validated_line):
        record = CallDataRecord(2)
        record.number = "+353876185584"
        return record


@pytest.fixture(autouse=True)
def mock_port(mock_serial_port):
    return mock_serial_port


@pytest.fixture
def mock_plugin(mocker):
    plugin = call_plugin(MockPlugin)
    mocked_runner = mocker.patch.object(running, "is_set")
    mocked_runner.side_effect = [True, False]
    mocker.patch.object(time, "sleep")
    yield plugin


def test_open_serial_exception(mock_serial, mock_plugin, mocker):
    mock_serial.open.side_effect = serial.SerialException
    timeout = mocker.spy(mock_plugin.timeout, "sleep")
    mock_serial.configure_mock(is_open=False)
    mock_plugin.run()

    assert timeout.called
    assert not mock_serial.is_open


def test_read_serial_line_exception(mock_serial, mock_plugin):
    mock_serial.readline.side_effect = serial.SerialException
    mock_plugin.run()

    assert mock_serial.readline.called
    assert not mock_serial.is_open
    assert mock_serial.close.called


def test_dateline(mock_serial, mock_plugin):
    mock_serial.readline.return_value = b"raw data line"
    mock_plugin.run()

    assert mock_serial.readline.called
    assert mock_serial.is_open
    assert not mock_serial.close.called


def test_failed_validate(mock_serial, mock_plugin, mocker):
    mock_serial.readline.return_value = b"raw data line"
    mocker.patch.object(mock_plugin, "validate", return_value=False)
    mock_plugin.run()

    assert mock_serial.readline.called
    assert mock_serial.is_open


def test_invalid_parse_object(mock_serial, mock_plugin, mocker):
    mock_serial.readline.return_value = b"raw data line"
    mocker.patch.object(mock_plugin, "parse", return_value=False)
    mock_plugin.run()

    assert mock_serial.readline.called
    assert mock_serial.is_open


@pytest.mark.parametrize("dockerized", [False, True])
def test_none_existing_port(mock_port, mock_settings, dockerized):
    mock_port.exists.return_value = False
    mock_settings(dockerized=dockerized)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        MockPlugin()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0
