# Standard Lib
import pkg_resources

# Local
import calllogger


# Installed Plugin EntryPoints
# https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entrypoint-objects
INSTALLED_PLUGINS = {plugin.name: plugin for plugin in pkg_resources.iter_entry_points("calllogger.plugins")}


if __name__ == "__main__":
    pass
