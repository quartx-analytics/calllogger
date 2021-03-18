# Standard lib
import sys

# Third Party
from decouple import config, undefined, UndefinedValueError
from requests.auth import AuthBase


class TokenAuth(AuthBase):
    """Requests Token authentication class."""

    def __init__(self, token: str):
        self.__token = token

    def __call__(self, req):
        req.headers["Authorization"] = f"Token {self.__token}"
        return req


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
        missing_settings = []
        self.settings = {k: v for k, v in self.__class__.__dict__.items() if not k.startswith("__")}
        for key, cast in self.__class__.__dict__.get('__annotations__', {}).items():
            default = self.settings.get(key, undefined)
            try:
                self.settings[key] = config(key.upper(), default, cast)
            except UndefinedValueError:
                msg = f"Missing required environment variable: {key.upper()}"
                missing_settings.append(msg)

        if missing_settings:
            for msg in missing_settings:
                print(msg)
            sys.exit()

    def __getitem__(self, item):
        return self.settings[item]

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(self.__class__.__name__, item))


settings = Settings()
