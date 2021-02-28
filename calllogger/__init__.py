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

# Third Party
import logging.config
import sentry_sdk
import environ

# Precast environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SENTRY_DSN=(str, ""),
)


def filter_events(event, _):
    """Filter sentry events."""
    return event


# Setup Sentry
if sentry_dsn := env("SENTRY_DSN"):
    sentry_sdk.init(
        sentry_dsn,
        release=__version__,
        before_send=filter_events,
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
            "level": "DEBUG" if env("DEBUG") else "INFO",
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
            "level": "DEBUG"
        }
    }
})
