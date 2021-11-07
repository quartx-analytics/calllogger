# Standard Lib
import time

# Third Party
import pytest
import serial

# Local
from calllogger.plugins import SerialPlugin
from calllogger.record import CallDataRecord
from ..common import call_plugin
from calllogger import stopped


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
    mocked_runner = mocker.patch.object(stopped, "is_set")
    mocked_runner.side_effect = [False, True]
    mocker.patch.object(time, "sleep")
    yield plugin


def test_open_serial_exception(mock_serial, mock_plugin, disable_sleep):
    mock_serial.open.side_effect = serial.SerialException
    mock_serial.configure_mock(is_open=False)
    mock_plugin.run()

    assert not mock_serial.is_open


def test_read_serial_line_exception(mock_serial, mock_plugin, mocker, disable_sleep):
    mock_serial.readline.side_effect = serial.SerialException
    spy_decode = mocker.spy(mock_plugin, "decode")
    mock_plugin.run()

    assert mock_serial.readline.called
    assert not mock_serial.is_open
    assert mock_serial.close.called
    assert not spy_decode.called


def test_dateline(mock_serial, mock_plugin):
    mock_serial.readline.return_value = b"raw data line"
    mock_plugin.run()

    assert mock_serial.readline.called
    assert mock_serial.is_open
    assert not mock_serial.close.called


def test_failed_decode(mock_serial, mock_plugin, mocker):
    mock_serial.readline.return_value = b"raw data line"
    mocker.patch.object(mock_plugin, "decode", side_effect=UnicodeDecodeError)
    spy_validate = mocker.spy(mock_plugin, "validate")
    mock_plugin.run()

    assert mock_serial.readline.called
    assert mock_serial.is_open
    assert not spy_validate.called


@pytest.mark.parametrize("return_value", [False, ""])
def test_failed_validate(mock_serial, mock_plugin, mocker, return_value):
    mock_serial.readline.return_value = b"raw data line"
    mocker.patch.object(mock_plugin, "validate", return_value=return_value)
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
    MockPlugin()
