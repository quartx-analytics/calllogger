# Standard lib
import sys

# Third Party
from decouple import config, undefined, UndefinedValueError
from requests.auth import AuthBase

__all__ = ["TokenAuth", "settings", "merge_settings"]


class TokenAuth(AuthBase):
    """Requests Token authentication class."""

    def __init__(self, token: str):
        self.__token = token

    def __call__(self, req):
        req.headers["Authorization"] = f"Token {self.__token}"
        return req


def merge_settings(cls, settings_store: dict = None, prefix="", **defaults):
    # Merge class, instance and defaults together
    settings_store.update(**cls.__dict__, **defaults)

    missing = []
    # Check if all settings with annotations have a environment variable set for them
    for key, cast in cls.__dict__.get("__annotations__", {}).items():
        default = settings_store.get(key, undefined)
        env_key = f"{prefix}_{key}".upper()
        try:
            setting = config(env_key, default, cast)
            settings_store[key] = setting
        except UndefinedValueError:
            missing.append(f"Missing required environment variable: {env_key}")

    # Report any settings the require an
    # environment variable to be set
    if missing:
        for msg in missing:
            print(msg)
        sys.exit()


class Settings:
    """
    Settings class that allows settings
    to be override by environment variables.
    """

    timeout: int = 3
    timeout_decay: float = 1.5
    max_timeout: int = 300
    queue_size: int = 1_000
    domain: str = "https://quartx.ie"
    debug: bool = False
    plugin: str = "SiemensHipathSerial"
    token: str = "dfdfs"

    def __init__(self):
        merge_settings(self.__class__, self.__dict__)


settings = Settings()
