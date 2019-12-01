# Standard lib
import pkgutil

# Package
from quartx_call_logger import settings, plugins

# Register all available plugins
prefix = plugins.__name__ + "."
for _, modname, _ in pkgutil.iter_modules(plugins.__path__, prefix):
    __import__(modname)


def main():
    """Start the specified plugin."""
    plugin = plugins.get_plugin(settings.PLUGIN_NAME)
    plugin_ins = plugin(**settings.PLUGIN_SETTINGS)
    plugin_ins.start()


# Start the call monitoring software
if __name__ == "__main__":
    main()
