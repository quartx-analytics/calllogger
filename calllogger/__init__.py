"""
MIT License

Copyright (c) 2020 QuartX

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__version__ = "0.4.0"

# Standard lib
import logging.config

# Third Party
import sentry_sdk
from sentry_sdk.integrations.threading import ThreadingIntegration
from decouple import config

# Setup Sentry
if sentry_dsn := config("SENTRY_DSN", ""):
    sentry_sdk.init(
        sentry_dsn,
        release=__version__,
        environment=config("ENVIRONMENT", "Testing"),
        integrations=[ThreadingIntegration(propagate_hub=True)],
    )

# Setup Logging
logging.config.dictConfig({
    "version": 1,
    "filters": {
        "only_messages": {
            "()": f"{__name__}.utils.OnlyMessages"
        }
    },
    "formatters": {
        "levelname": {
            "format": "%(levelname)s: %(message)s",
        }
    },
    "handlers": {
        "console_messages": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["only_messages"],
            "formatter": "levelname",
        },
        "console_errors": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "levelname",
            "level": "WARNING",
        }
    },
    "loggers": {
        __name__: {
            "handlers": ["console_messages", "console_errors"],
            "level": "DEBUG" if config("DEBUG", False, cast=bool) else "INFO",
        }
    }
})

__all__ = ["CallDataRecord", "BasePlugin", "SerialPlugin"]
from .record import CallDataRecord
from .plugins import (
    BasePlugin,
    SerialPlugin,
)
