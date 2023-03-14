# Standard library
from typing import Type, Union
import logging
import sys

# Local
from calllogger.plugins.base import BasePlugin
from calllogger.plugins.serial import SerialPlugin

# Internal Plugins
from calllogger.plugins.internal.mockcalls import MockCalls
from calllogger.plugins.internal.siemens_serial import SiemensHipathSerial

__all__ = ["BasePlugin", "SerialPlugin", "get_plugin"]
logger = logging.getLogger(__name__)
installed = {}


# TODO: Find a good solution for supporting external plugins
def register_plugins(*plugins: Type[BasePlugin]):
    """Register internal plugins."""
    for plugin in plugins:
        name = plugin.__name__
        installed[name.lower()] = installed[str(plugin.id)] = plugin
        logger.debug("Plugin Registered: %s - %s", name, plugin.__doc__)


def get_plugin(selected_plugin: Union[str, int]):
    """Return the selected plugin."""
    if plugin := installed.get(str(selected_plugin).lower()):
        return plugin
    else:
        print("Specified plugin not found:", selected_plugin)
        print("Available plugins are:")
        for plugin in installed.values():
            print(f"--> {plugin.id} {plugin.__name__} - {plugin.__doc__}")
        sys.exit(0)


# Register Internal and External Plugins
register_plugins(MockCalls, SiemensHipathSerial)
