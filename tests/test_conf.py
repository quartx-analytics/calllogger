# Standard Lib
from pathlib import PosixPath

# Third Party
from pytest_mock import MockerFixture
import pytest

# Local
from calllogger import conf, settings, utils


class MockSettings:
    test1: int = 1
    test2: str = "1"
    test3: bool = True
    test4: float = 1.1
    test5 = "1"
    test6: str
    test7: conf.b64 = ""


@pytest.fixture
def clear_settings_cache():
    """Clear datastore cached_property."""
    def worker(attr: str):
        if hasattr(settings, attr):
            delattr(settings, attr)
        yield
        if hasattr(settings, attr):
            delattr(settings, attr)
    return worker


class TestMergeSettings:
    def test_environment_values(self, mock_env):
        mock_env(
            TEST1="5", TEST2="5", TEST3="false",
            TEST4="5.5", TEST5="5", TEST6="5",
        )
        mocked_settings = MockSettings()
        conf.merge_settings(mocked_settings)

        assert mocked_settings.test1 == 5
        assert mocked_settings.test2 == "5"
        assert mocked_settings.test3 is False
        assert mocked_settings.test4 == 5.5
        # This should not have been changed as
        # test5 did not have any annotations
        assert mocked_settings.test5 == "1"
        # Test6 is a required variable
        assert mocked_settings.test6 == "5"

    def test_missing_required(self):
        """Test if system exit is call after missing required error."""
        mocked_settings = MockSettings()
        with pytest.raises(SystemExit):
            conf.merge_settings(mocked_settings)

    def test_override_defaults(self):
        mocked_settings = MockSettings()
        conf.merge_settings(mocked_settings, test5="test", test6="test")

        # Test5 can be override this way
        assert mocked_settings.test5 == "test"
        # This time SystemExit should not be raised for missing required
        assert mocked_settings.test6 == "test"

    def test_prefix(self, mock_env):
        mock_env(PLUGIN_TEST1="5", PLUGIN_TEST3="0", PLUGIN_TEST6="test")
        mocked_settings = MockSettings()
        conf.merge_settings(mocked_settings, prefix="PLUGIN_")

        assert mocked_settings.test1 == 5
        assert mocked_settings.test3 is False
        assert mocked_settings.test6 == "test"

    def test_cast_fail(self, mock_env):
        mock_env(TEST1="int", TEST6="test")
        mocked_settings = MockSettings()
        with pytest.raises(SystemExit):
            conf.merge_settings(mocked_settings)

    @pytest.mark.parametrize("env_string", [
        "testdata",
        "ZW5jb2RlZDo=dGVzdGRhdGE=",
    ])
    def test_b64decode(self, env_string, mock_env):
        mock_env(TEST7=env_string, TEST6="test")
        mocked_settings = MockSettings()
        conf.merge_settings(mocked_settings)

        assert mocked_settings.test7 == "testdata"

    @pytest.mark.parametrize("env_string", [
        "ZW5jb2RlZDo=ZW5jb2RlZDo",
        "ZW5jb2RlZDo=dfdd34hgf",
    ])
    def test_b64decode_error(self, env_string, mock_env):
        """Test if system exit is call after missing required error."""
        mock_env(TEST7=env_string, TEST6="test")
        mocked_settings = MockSettings()
        with pytest.raises(SystemExit):
            conf.merge_settings(mocked_settings)


class TestDataStoreSettings:
    @pytest.fixture(autouse=True)
    def clear_cache(self, clear_settings_cache):
        yield from clear_settings_cache("datastore")

    def test_env_set(self, mock_env):
        mock_env(DATA_LOCATION="/")
        assert settings.datastore == PosixPath("/")

    def test_appdirs(self):
        assert str(settings.datastore).endswith("/.local/share/quartx-calllogger")


class TestGetIdentifier:
    """Test get_identifier function."""

    # Example mac address
    mac_addr = "CB:BB:27:BF:51:5C"

    @pytest.fixture(autouse=True)
    def clear_cache(self, clear_settings_cache):
        """Clear identifier cached_property."""
        yield from clear_settings_cache("identifier")

    def test_stored(self, mocker: MockerFixture):
        """Test fetching identifier from datastore."""
        mocked_stored = mocker.patch.object(settings, "_identifier_store")
        mocked_stored.exists.return_value = True

        mocked_read = mocker.patch.object(utils, "read_datastore")
        mocked_read.return_value = self.mac_addr

        identifier = settings.identifier
        assert mocked_stored.exists.called
        assert mocked_read.called
        assert identifier == self.mac_addr

    def test_from_network(self, mocker: MockerFixture, disable_write_datastore):
        """Test fetching identifier from network device."""
        # Force identifier_store to not exist
        mocked_stored = mocker.patch.object(settings, "_identifier_store")
        mocked_stored.exists.return_value = False
        # Return known mac address from get_mac_address function from getmac lib
        mocked_get_mac = mocker.patch.object(conf, "get_mac_address", return_value=self.mac_addr)

        identifier = settings.identifier
        assert mocked_get_mac.called
        assert disable_write_datastore.called
        assert identifier == self.mac_addr

    @pytest.mark.parametrize("invalid_mac", ["00:00:00:00:00:00", None])
    def test_invalid_identifier(self, mocker: MockerFixture, invalid_mac, disable_write_datastore):
        """Test that a invalid identifier returns 'None'."""
        # Force identifier_store to not exist
        mocked_stored = mocker.patch.object(settings, "_identifier_store")
        mocked_stored.exists.return_value = False
        # Return known mac address from get_mac_address function from getmac lib
        mocked_get_mac = mocker.patch.object(conf, "get_mac_address", return_value=invalid_mac)

        with pytest.raises(SystemExit):
            _ = settings.identifier
        assert mocked_get_mac.called
        assert disable_write_datastore.called is False
