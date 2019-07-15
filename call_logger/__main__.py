# Package
from call_logger import config, plugins


def main():
    plugin_name = config["settings"]["phone_system"]
    plugin_settings = config.get(plugin_name, fallback=None)
    timeout_settings = {
        "timeout": config["settings"]["timeout"],
        "max_timeout": config["settings"]["max_timeout"],
        "decay": config["settings"]["decay"]
    }

    # Select phone system plugin that is used to fetch call logs
    plugin = plugins.get_plugin(plugin_name)

    # Start the plugin and monitor for call logs
    plugin_ins = plugin(**plugin_settings, **timeout_settings)
    plugin_ins.run()


# Start the call monitoring software
if __name__ == "__main__":
    main()
