# Standard Lib
import signal

# Third Party
from pytest_mock import MockerFixture
import sentry_sdk
import pytest

# Local
from calllogger import __main__ as entrypoint


def test_set_sentry_user(mocker: MockerFixture):
    """
    Test that set_sentry_user takes client data
    and converts it to what sentry expects.
    """
    mocked_set_user = mocker.patch.object(sentry_sdk, "set_user")
    client_data = {
        "id": 1,
        "name": "TestClient",
        "email": "testclient@gmail.com",
    }
    expected_data = {
        "id": 1,
        "username": "TestClient",
        "email": "testclient@gmail.com",
    }

    entrypoint.set_sentry_user(client_data)
    mocked_set_user.assert_called_with(expected_data)


@pytest.mark.parametrize("return_data", [KeyboardInterrupt, "testdata"])
def test_graceful_exception(mocker: MockerFixture, return_data):
    spy_running_clear = mocker.spy(entrypoint.running, "clear")
    spy_terminate = mocker.spy(entrypoint, "terminate")

    @entrypoint.graceful_exception
    def worker():
        if isinstance(return_data, str):
            return return_data
        else:
            raise KeyboardInterrupt

    worker()
    assert spy_running_clear.called
    if isinstance(return_data, Exception):
        spy_terminate.assert_called_with(signal.SIGINT)


def test_main_loop(mocker: MockerFixture):
    mocked_cdrworker = mocker.patch.object(entrypoint.api, "CDRWorker")
    mocked_info = mocker.patch.object(entrypoint.api, "get_owner_info")
    mocked_get_token = mocker.patch.object(entrypoint, "get_token")
    mock_plugin = mocker.MagicMock

    entrypoint.main_loop(mock_plugin)


