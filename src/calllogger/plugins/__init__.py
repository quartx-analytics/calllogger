# Standard library
from typing import Type
import pkg_resources
import logging

# Local
from calllogger.plugins.base import BasePlugin
from calllogger.plugins.serial import SerialPlugin

# Internal Plugins
from calllogger.plugins.internal.mockcalls import MockCalls

__all__ = ["BasePlugin", "SerialPlugin", "installed"]
logger = logging.getLogger(__name__)
installed = {}


def register_plugins(*plugins: Type[BasePlugin]):
    """Register internal plugins."""
    for plugin in plugins:
        name = plugin.__name__
        installed[name.lower()] = plugin
        logger.debug("Plugin Registered: %s - %s", name, plugin.__doc__)


def find_plugins() -> dict:
    """
    Return a dict of all the installed plugins.
    The name of the plugin as the key.
    """
    external_plugins = pkg_resources.iter_entry_points("calllogger.plugin")
    plugins = (plugin.get_class() for plugin in external_plugins)
    register_plugins(*plugins)
    return installed


# Register Internal and External Plugins
register_plugins(MockCalls)
find_plugins()
