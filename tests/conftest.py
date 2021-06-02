# Standard Lib
import logging

# Third Party
import os

import pytest
import serial

# Local
from calllogger.plugins.serial import SerialPlugin
from calllogger import running


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.WARNING)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def disable_sleep(mocker):
    return mocker.patch("time.sleep")


@pytest.fixture
def mock_running(mocker):
    mocked = mocker.patch.object(running, "is_set")
    mocked.return_value = True
    yield mocked


@pytest.fixture
def mock_serial_port(mocker):
    mocked = mocker.patch.object(SerialPlugin, "port", spec=True)
    mocked.__str__.return_value = "/port"
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
    def worker(**kwargs):
        for key, val in kwargs.items():
            mocker.patch(
                f"calllogger.conf.Settings.{key}",
                new_callable=mocker.PropertyMock,
                return_value=val,
            )
    yield worker


@pytest.fixture
def mock_env():
    # Keep track of original key, value
    tracker = []

    def env_mocker(**kwargs):
        for key, val in kwargs.items():
            key = key.upper()
            org_value = os.environ.get(key, None)
            tracker.append((key, org_value))
            os.environ[key] = str(val)

    yield env_mocker

    # Reset environment state
    for k, v in tracker:
        # Remove key if there is no original value for it
        if v is None and k in os.environ:
            del os.environ[k]

        # Replace key with original value
        elif v is not None:
            os.environ[k] = v
