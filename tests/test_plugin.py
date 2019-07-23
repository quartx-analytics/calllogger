import pytest

# Package
from call_logger import plugins
from call_logger.plugins.siemens_hipath_serial import SiemensHipathSerial


# noinspection PyUnusedLocal,PyRedeclaration,PyAbstractClass
def test_dup_plugin():
    """Test that DuplicatePlugin is raised when Plugin name already exists."""
    with pytest.raises(plugins.DuplicatePlugin):
        class Test1(plugins.Plugin):
            pass

        class Test1(plugins.Plugin):
            pass


def test_get_plugin_exists():
    plugin = plugins.get_plugin("SiemensHipathSerial")
    assert plugin is SiemensHipathSerial


def test_get_plugin_non_exist():
    with pytest.raises(KeyError):
        plugins.get_plugin("SiemensHipath")
