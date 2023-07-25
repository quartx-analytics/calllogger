# Standard lib
from queue import SimpleQueue

# Third Party
from pytest_mock import MockerFixture
import pytest

# Local
from calllogger import plugins, settings
from calllogger.record import CallDataRecord


class MockedPlugin(plugins.BasePlugin):
    id = 1
    _queue = SimpleQueue()

    def entrypoint(self):
        pass


def test_register_plugins(mocker: MockerFixture):
    mocker.patch.object(plugins, "installed", {})
    plugins.register_plugins(MockedPlugin)

    assert plugins.installed
    assert "mockedplugin" in plugins.installed
    assert str(MockedPlugin.id) in plugins.installed
    assert plugins.installed["mockedplugin"] is MockedPlugin


class TestGetPlugin:
    """Test plugins.get_plugin function."""

    @pytest.fixture
    def register_plugin(self, mocker: MockerFixture):
        mocker.patch.object(plugins, "installed", {})
        plugins.register_plugins(MockedPlugin)

    @pytest.mark.parametrize("plugin_id", [MockedPlugin.__name__, MockedPlugin.id])
    def test_plugin_found(self, register_plugin, plugin_id):
        """Test that get_plugin returns the plugin with the given name."""
        plugin = plugins.get_plugin(plugin_id)
        assert plugin is MockedPlugin

    @pytest.mark.parametrize("value", ["pluginnotfound", ""])
    def test_plugin_not_found(self, register_plugin, value):
        """Test that systemexit is raised if plugin is now found."""
        with pytest.raises(SystemExit):
            plugins.get_plugin(value)


@pytest.fixture
def mock_record():
    return CallDataRecord(call_type=1)


class TestBasePluginPush:
    def test_basic_push(self, mock_record):
        """Test the push adds record to queue."""
        plugin = MockedPlugin()
        assert plugin._queue.qsize() == 0
        plugin.push(mock_record)
        assert plugin._queue.qsize() == 1

    def test_queue_full_blocked(self, mock_record, mocker, disable_sleep):
        """Test that push blocks and never pushes as long as the queue is full."""
        plugin = MockedPlugin()
        mocked = mocker.patch.object(plugin, "_queue", spec=SimpleQueue)
        mocked.qsize.return_value = settings.queue_size
        disable_sleep.side_effect = [False, True]

        assert plugin._queue.qsize() == settings.queue_size
        plugin.push(mock_record)
        assert plugin._queue.qsize() == settings.queue_size
        assert mocked.put.called is False

    def test_queue_full_unblocked(self, mock_record, mocker, disable_sleep):
        """Test that push blocks and but gets unblocked when queue size drops."""
        plugin = MockedPlugin()
        mocked = mocker.patch.object(plugin, "_queue", spec=SimpleQueue)

        def unblocker(_):
            """
            This function will drop the size of queue to
            simulate that the queue droped while waiting.
            """
            mocked.qsize.return_value -= 25
            return False  # This will trigger the loop to continue

        def put(_):
            mocked.qsize.return_value += 1

        mocked.qsize.return_value = settings.queue_size
        mocked.put.side_effect = put
        disable_sleep.side_effect = unblocker

        assert plugin._queue.qsize() == settings.queue_size
        plugin.push(mock_record)
        assert plugin._queue.qsize() == settings.queue_size - 25 + 1
        assert mocked.put.called is True


class TestBasePluginSettings:

    def test_with_default_value_in_init(self, mock_env):
        """Test that a plugin setting with default value gets changed and is available in init."""

        class MockedPluginSetting(plugins.BasePlugin):
            id = 1
            _queue = SimpleQueue()
            test_value: str = "false"

            def __init__(self):
                super().__init__()
                self.value = self.test_value

            def entrypoint(self):
                pass

        assert_value = "true"
        mock_env(plugin_test_value=assert_value)
        plugin = MockedPluginSetting()
        assert plugin.test_value == assert_value
        assert plugin.value == assert_value

    def test_with_no_default_value_in_init(self, mock_env):
        """Test that a plugin setting with no default value gets set and is available in init."""

        class MockedPluginSetting(plugins.BasePlugin):
            id = 1
            _queue = SimpleQueue()
            test_value: str

            def __init__(self):
                super().__init__()
                self.value = self.test_value

            def entrypoint(self):
                pass

        assert_value = "true"
        mock_env(plugin_test_value=assert_value)
        plugin = MockedPluginSetting()
        assert plugin.test_value == assert_value
        assert plugin.value == assert_value
