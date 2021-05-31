# Standard Lib
import logging

# Third Party
import pytest
import serial

# Local
from calllogger.plugins.serial import SerialPlugin
from calllogger.conf import settings


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.WARNING)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def mock_serial_port(mocker):
    mocked = mocker.patch.object(SerialPlugin, "port", spec=True)
    mocked.exists.return_value = True
    yield mocked


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
    mocked.return_value.configure_mock(is_open=True)
    yield mocked.return_value


@pytest.fixture
def mock_settings(mocker):
    def mock_settings(key, value):
        mocked = mocker.patch.object(settings, key, new_callable=mocker.PropertyMock)
        mocked.return_value = value
    yield mock_settings
