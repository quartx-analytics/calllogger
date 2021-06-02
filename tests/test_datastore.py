# Standard Lib
from pathlib import PosixPath
import base64

# Third Party
from pytest_mock import MockerFixture
import pytest

# Local
from calllogger import datastore
from calllogger.utils import TokenAuth


@pytest.fixture
def disable_write_datastore(mocker: MockerFixture):
    return mocker.patch.object(datastore, "write_datastore")


class TestReadWrite:
    """Test read_datastore and write_datastore functions."""

    def test_read(self, mocker: MockerFixture):
        """Test that datastore reads and decodes correctly."""
        encoded_data = base64.b64encode(b"testdata")
        mocked_open = mocker.patch.object(PosixPath, "open", mocker.mock_open(read_data=encoded_data))

        path = PosixPath("/data")
        value = datastore.read_datastore(path)

        mocked_open.assert_called_with("rb")
        assert mocked_open.return_value.read.called
        assert value == "testdata"

    def test_write(self, mocker: MockerFixture):
        """Test that datastore writes encoded data."""
        encoded_data = base64.b64encode(b"testdata")
        mocked_open = mocker.patch.object(PosixPath, "open", mocker.mock_open())

        path = PosixPath("/data")
        datastore.write_datastore(path, "testdata")

        mocked_open.assert_called_with("wb")
        mocked_open.return_value.write.assert_called_with(encoded_data)


class TestGetIdentifier:
    """Test get_identifier function."""

    # Example mac address
    mac_addr = "CB:BB:27:BF:51:5C"

    def test_stored(self, mocker: MockerFixture):
        """Test fetching identifier from datastore."""
        mocked_stored = mocker.patch.object(datastore, "identifier_store")
        mocked_stored.exists.return_value = True

        mocked_read = mocker.patch.object(datastore, "read_datastore")
        mocked_read.return_value = self.mac_addr

        identifier = datastore.get_identifier()
        assert mocked_stored.exists.called
        assert mocked_read.called
        assert identifier == self.mac_addr

    def test_from_network(self, mocker: MockerFixture, disable_write_datastore):
        """Test fetching identifier from network device."""
        # Force identifier_store to not exist
        mocked_stored = mocker.patch.object(datastore, "identifier_store")
        mocked_stored.exists.return_value = False
        # Return known mac address from get_mac_address function from getmac lib
        mocked_get_mac = mocker.patch.object(datastore, "get_mac_address", return_value=self.mac_addr)

        identifier = datastore.get_identifier()
        assert mocked_get_mac.called
        assert disable_write_datastore.called
        assert identifier == self.mac_addr

    @pytest.mark.parametrize("invalid_mac", ["00:00:00:00:00:00", None])
    def test_invalid_identifier(self, mocker: MockerFixture, invalid_mac):
        """Test that a invalid identifier returns 'None'."""
        # Force identifier_store to not exist
        mocked_stored = mocker.patch.object(datastore, "identifier_store")
        mocked_stored.exists.return_value = False
        # Disable writeing
        mocked_write = mocker.patch.object(datastore, "write_datastore")
        # Return known mac address from get_mac_address function from getmac lib
        mocked_get_mac = mocker.patch.object(datastore, "get_mac_address", return_value=invalid_mac)

        identifier = datastore.get_identifier()
        assert mocked_get_mac.called
        assert mocked_write.called is False
        assert identifier is None


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
        mocked_spy = mocker.spy(datastore, "token_store")
        datastore.revoke_token()
        assert mocked_spy.unlink.called

    def test_token_in_env(self, mock_env):
        mock_env(TOKEN=self.token)
        tokenauth = datastore.get_token()

        assert isinstance(tokenauth, TokenAuth)
        assert tokenauth.token == self.token

    def test_stored_token(self, mocker: MockerFixture):
        mocked_stored = mocker.patch.object(datastore, "token_store")
        mocked_stored.exists.return_value = True
        mocked_read = mocker.patch.object(datastore, "read_datastore")
        mocked_read.return_value = self.token

        tokenauth = datastore.get_token()

        assert mocked_stored.exists.called
        assert mocked_read.called
        assert isinstance(tokenauth, TokenAuth)
        assert tokenauth.token == self.token


class TestRequestToken:
    """Test the request_token part of the get_token function."""

    # Example mac address
    mac_addr = "00:1B:44:11:3A:B7"
    # Test token
    token = "testtoken"

    @pytest.fixture
    def mock_identifier(self, mocker: MockerFixture):
        return mocker.patch.object(datastore, "get_identifier", return_value=self.mac_addr)

    @pytest.fixture
    def mock_link_device(self, mocker: MockerFixture):
        return mocker.patch.object(datastore.api, "link_device", return_value=self.token)

    @pytest.fixture(autouse=True)
    def disable_env_and_store(self, mocker: MockerFixture, mock_env):
        """Ensure that token env and token store does not exist."""
        mocked_stored = mocker.patch.object(datastore, "token_store")
        mocked_stored.exists.return_value = False
        mock_env(token="")
        yield

    def test_link_device(self, mock_identifier, mock_link_device, disable_write_datastore):
        """Test that request_token returns a valid token."""
        tokenauth = datastore.get_token()
        assert mock_link_device.called
        assert disable_write_datastore.called
        assert tokenauth.token == self.token

    def test_failed_link_device(self, mock_identifier, mock_link_device):
        mock_link_device.return_value = None
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            datastore.get_token()
            assert mock_identifier.called
            assert mock_link_device.called
            assert pytest_wrapped_e.value.code == 0

    def test_invalid_identifier(self, mock_identifier):
        mock_identifier.return_value = None
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            datastore.get_token()
            assert mock_identifier.called
            assert pytest_wrapped_e.value.code == 0

    def test_valid_identifier_but_no_reg_key(self, mock_identifier, mock_link_device, mock_settings):
        mock_settings(reg_key="")

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            datastore.get_token()
            assert mock_identifier.called
            assert not mock_link_device.called
            assert pytest_wrapped_e.value.code == 0
