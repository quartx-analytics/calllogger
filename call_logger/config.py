# Standard lib
import yaml
import os

# Third party
import appdirs

# Location for user config files and logs
CONFIG_DIR = appdirs.site_config_dir("quartx")
BASE_CONFIG = os.path.join(os.path.dirname(__file__), "data", "default.yml")
USER_CONFIG = os.path.join(CONFIG_DIR, "call-logger.yml")


def update_recursively(base, custom):
    """Recursively update a dict of configuration settings."""
    for key, val in custom.items():
        if isinstance(val, dict):
            update_recursively(base[key], val)
        else:
            base[key] = val


def compile_settings() -> dict:
    with open(BASE_CONFIG) as stream:
        settings = yaml.safe_load(stream.read())

    if os.path.exists(USER_CONFIG):
        with open(USER_CONFIG) as stream:
            custom_config = yaml.safe_load(stream.read())

            # Validate that token is set
            if "settings" not in custom_config or "token" not in custom_config["settings"]:
                raise RuntimeError("missing required token. please set token in config file: %s", USER_CONFIG)

            # Recursively update base config
            update_recursively(settings, custom_config)

    return settings
