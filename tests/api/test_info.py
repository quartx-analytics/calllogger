# Standard Lib
import os
import socket

# Third Party
import pytest
import requests
import sentry_sdk
from pytest_mock import MockerFixture

# Local
from calllogger.api import info
from calllogger.utils import TokenAuth
from calllogger import stopped, settings


class TestGetPrivateIP:
    def test_get_private_ip(self, mocker):
        """Test that a local ip address is returned."""
        mocker.patch.object(socket.socket, "connect")
        mocker.patch.object(socket.socket, "getsockname", return_value=("192.168.1.1", 44951))

        ip = info.get_private_ip()
        assert ip == "192.168.1.1"

    def test_get_private_ip_error(self, mocker):
        """Test that an empty string is return on error."""
        mocker.patch.object(socket.socket, "connect", side_effect=OSError)
        ip = info.get_private_ip()
        assert ip == ""


class TestGetClientInfo:
    @pytest.mark.parametrize("get_private_ip", ["192.168.1.1", None])
    @pytest.mark.parametrize("identifier", ["C4:11:0B:0F:F5:C5", None])
    def test_get_owner_info(self, requests_mock, mocker, identifier, get_private_ip):
        tokenauth = TokenAuth("token")
        mocker.patch.object(stopped, "is_set", return_value=False)
        mocker.patch.object(info, "get_private_ip", return_value=get_private_ip)
        expected_resp = {'id': 1, 'name': 'Test', 'email': 'test@test.com', 'settings': {}}
        mocked_request = requests_mock.post(info.info_url, status_code=200, json=expected_resp)
        resp = info.get_client_info(tokenauth, identifier)

        assert mocked_request.called
        assert isinstance(resp, info.ClientInfo)
        for key, val in expected_resp.items():
            assert getattr(resp, key) == val
            assert resp[key] == val

    def test_request_error(self, mocker, requests_mock, disable_sleep):
        tokenauth = TokenAuth("token")
        mocker.patch.object(stopped, "is_set", return_value=False)
        mocker.patch.object(info, "get_private_ip", return_value="192.168.1.1")
        mocked_request = requests_mock.post(info.info_url, status_code=400)
        with pytest.raises(requests.HTTPError):
            info.get_client_info(tokenauth, "C4:11:0B:0F:F5:C5")

        assert mocked_request.called

    def test_restart_requested(self, mocker, requests_mock):
        tokenauth = TokenAuth("token")
        spy_stopped = mocker.spy(info.stopped, "set")
        mocker.patch.object(stopped, "is_set", return_value=False)
        mocker.patch.object(info, "get_private_ip", return_value="192.168.1.1")
        expected_resp = {'id': 1, 'name': 'Test', 'email': 'test@test.com', "restart": True, 'settings': {}}
        mocked_request = requests_mock.post(info.info_url, status_code=200, json=expected_resp)
        resp = info.get_client_info(tokenauth, "C4:11:0B:0F:F5:C5", checkin=True)

        spy_stopped.assert_called_with(1)
        assert mocked_request.called
        assert isinstance(resp, info.ClientInfo)
        for key, val in expected_resp.items():
            assert getattr(resp, key) == val
            assert resp[key] == val


def test_set_sentry_user(mocker: MockerFixture):
    """
    Test that set_sentry_user takes client data
    and converts it to what sentry expects.
    """
    mocked_set_user = mocker.patch.object(sentry_sdk, "set_user")
    client_data = info.ClientInfo({
        "id": 1,
        "name": "TestClient",
        "email": "testclient@gmail.com",
    })
    expected_data = {
        "id": 1,
        "username": "TestClient",
        "email": "testclient@gmail.com",
    }

    info.set_sentry_user(client_data)
    mocked_set_user.assert_called_with(expected_data)


class TestUpdateSettings:
    def test_overrides(self):
        """Test that setting get changed."""
        # Remove existing env value if exsits
        val = os.environ.pop("TIMEOUT", None)
        try:
            settings.timeout = 3
            assert settings.timeout == 3
            info.update_settings(timeout=5)
            assert settings.timeout == 5
        finally:
            if val is not None:
                os.environ["TIMEOUT"] = val

    def test_override_disabled_by_env(self):
        """Test that settings don't get changed if there is a env for givne setting."""
        settings.timeout = 3
        assert settings.timeout == 3
        os.environ["TIMEOUT"] = "3"
        info.update_settings(timeout=5)
        assert settings.timeout == 3


def test_checkin_setup(mocker):
    mocked = mocker.patch.object(info, "ThreadTimer", autospec=True)
    tokenauth = TokenAuth("token")
    info.setup_client_checkin(tokenauth, "C4:11:0B:0F:F5:C5")
    assert mocked.return_value.start.called
