# Standard lib
import sys

# Third Party
from decouple import config, undefined, UndefinedValueError


__all__ = ["settings", "merge_settings"]


def merge_settings(cls, settings_store: dict, prefix="", **defaults):
    # Merge class, instance and defaults together
    defaults_store = dict(**cls.__dict__, **defaults)
    prefix = f"{prefix}_" if prefix else ""
    settings_store.update(defaults)
    errors = []

    # Check if all settings with annotations have a environment variable set for them
    for key, cast in cls.__dict__.get("__annotations__", {}).items():
        default = defaults_store.get(key, undefined)
        env_key = f"{prefix}{key}"
        try:
            setting = config(env_key.upper(), default, cast)
            settings_store[key] = setting
        except UndefinedValueError:
            errors.append(f"Missing required environment variable: {env_key}")
        except (ValueError, TypeError):
            errors.append(f"Invalid type for setting '{env_key}', expecting '{cast.__name__}'")

    # Report any error to user and quit
    if errors:
        for msg in errors:
            print(msg)
        sys.exit()


class Settings:
    """
    Settings class that allows settings
    to be override by environment variables.
    """

    #: Timeout in seconds to sleep on errors.
    timeout: int = 3
    #: Multiplier that increases the timeout on continuous errors.
    timeout_decay: float = 1.5
    #: The max timeout can be after continuous decay.
    max_timeout: int = 300
    #: Size of the call queue
    queue_size: int = 1_000
    # The domain to send the call logs to, used in development.
    domain: str = "https://quartx.ie"
    #: Set to true to enable debug logging.
    debug: bool = False
    #: Required -  The name of the plugin to use.
    plugin: str

    def __init__(self):
        merge_settings(self.__class__, self.__dict__)

    def __repr__(self):
        clean = {key: val for key, val in self.__dict__.items() if not key.startswith("__")}
        return repr(clean)


settings = Settings()
