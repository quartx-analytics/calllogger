# Third Party
from pytest_mock import MockerFixture
import pytest

# Local
from calllogger import auth, utils
from calllogger.utils import TokenAuth


class TestGetToken:
    """Test get_token & revoke_token functions."""
    # Test token
    token = "testtoken"

    @pytest.fixture(autouse=True)
    def clear_token(self, mock_env):
        """Ensure that token env does not exist."""
        mock_env(token="")
        yield

    def test_revoke_token(self, mocker: MockerFixture):
        """Test that token_store unlink is called"""
        mocked_spy = mocker.spy(auth, "token_store")
        auth.revoke_token()
        assert mocked_spy.unlink.called

    def test_token_in_env(self, mock_env):
        mock_env(TOKEN=self.token)
        tokenauth = auth.get_token()

        assert isinstance(tokenauth, TokenAuth)
        assert tokenauth.token == self.token

    def test_stored_token(self, mocker: MockerFixture):
        mocked_stored = mocker.patch.object(auth, "token_store")
        mocked_stored.exists.return_value = True
        mocked_read = mocker.patch.object(utils, "read_datastore")
        mocked_read.return_value = self.token

        tokenauth = auth.get_token()

        assert mocked_stored.exists.called
        assert mocked_read.called
        assert isinstance(tokenauth, TokenAuth)
        assert tokenauth.token == self.token


class TRequestToken:
    """Test the request_token part of the get_token function."""

    # Example mac address
    mac_addr = "00:1B:44:11:3A:B7"
    # Test token
    token = "testtoken"

    @pytest.fixture
    def mock_identifier(self, mock_setting):
        return mock_setting("identifier", self.mac_addr)

    @pytest.fixture
    def mock_link_device(self, mocker: MockerFixture):
        return mocker.patch.object(auth.api, "link_device", return_value=self.token)

    @pytest.fixture(autouse=True)
    def set_reg_key(self, mock_settings):
        mock_settings(reg_key="kdkfjo23ik98u098u")
        return

    @pytest.fixture(autouse=True)
    def disable_env_and_store(self, mocker: MockerFixture, mock_env):
        """Ensure that token env and token store does not exist."""
        mocked_stored = mocker.patch.object(auth, "token_store")
        mocked_stored.exists.return_value = False
        mock_env(token="")
        yield

    def test_link_device(self, mock_identifier, mock_link_device, disable_write_datastore):
        """Test that request_token returns a valid token."""
        tokenauth = auth.get_token()
        assert mock_link_device.called
        assert disable_write_datastore.called
        assert tokenauth.token == self.token

    def test_failed_link_device(self, mock_identifier, mock_link_device):
        mock_link_device.return_value = None
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            auth.get_token()
            assert mock_identifier.called
            assert mock_link_device.called
            assert pytest_wrapped_e.value.code == 0

    def test_invalid_identifier(self, mock_identifier):
        mock_identifier.return_value = None
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            auth.get_token()
            assert mock_identifier.called
            assert pytest_wrapped_e.value.code == 0

    def test_valid_identifier_but_no_reg_key(self, mock_identifier, mock_link_device, mock_settings):
        mock_settings(reg_key="")

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            auth.get_token()
            assert mock_identifier.called
            assert not mock_link_device.called
            assert pytest_wrapped_e.value.code == 0
