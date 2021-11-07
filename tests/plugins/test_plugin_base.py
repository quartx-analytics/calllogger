# Third Party
from pytest_mock import MockerFixture
import pytest

# Local
from calllogger import plugins


class MockedPlugin(plugins.BasePlugin):
    id = 1

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
