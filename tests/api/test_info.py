# Standard Lib
import socket

# Third Party
import pytest
import sentry_sdk
from pytest_mock import MockerFixture

# Local
from calllogger.api import info
from calllogger.utils import TokenAuth
from calllogger import stopped


def test_get_private_ip(mocker):
    """Test that a local ip address is returned."""
    mocker.patch.object(socket.socket, "connect")
    mocker.patch.object(socket.socket, "getsockname", return_value=("192.168.1.1", 44951))

    ip = info.get_private_ip()
    assert ip == "192.168.1.1"


def test_get_private_ip_error(mocker):
    """Test that an empty string is return on error."""
    mocker.patch.object(socket.socket, "connect", side_effect=OSError)
    ip = info.get_private_ip()
    assert ip == ""


@pytest.mark.parametrize("get_private_ip", ["192.168.1.1", None])
@pytest.mark.parametrize("identifier", ["C4:11:0B:0F:F5:C5", None])
def test_get_owner_info(requests_mock, mocker, identifier, get_private_ip):
    tokenauth = TokenAuth("token")
    mocked_running = mocker.patch.object(stopped, "is_set")
    mocked_running.return_value = False
    mocker.patch.object(info, "get_private_ip", return_value=get_private_ip)
    expected_resp = {'id': 1, 'name': 'Test', 'email': 'test@test.com'}
    mocked_request = requests_mock.post(info.info_url, status_code=200, json=expected_resp)
    resp = info.get_client_info(tokenauth, identifier)

    assert mocked_request.called
    assert resp == expected_resp


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

    info.set_sentry_user(client_data)
    mocked_set_user.assert_called_with(expected_data)
