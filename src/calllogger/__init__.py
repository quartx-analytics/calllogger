# -*- coding: utf-8 -*-
# Copyright: (c) 2020 - 2021 Quartx (info@quartx.ie)
#
# License: GPLv2, see LICENSE for more details
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

__all__ = ["__version__", "__package__", "running", "settings"]

# Standard lib
from importlib.metadata import version
import logging.config
import threading

# Third Party
import sentry_sdk
from sentry_sdk.integrations.threading import ThreadingIntegration

# Local
from calllogger.conf import Settings

__package__ = "quartx-calllogger"
__version__ = version(__package__)
running = threading.Event()
settings = Settings()

# Setup Sentry
sentry_sdk.init(
    settings.sentry_dsn,
    release=__version__,
    environment=settings.environment,
    integrations=[ThreadingIntegration(propagate_hub=True)],
    max_breadcrumbs=25,
)

# Setup Logging
logging.config.dictConfig({
    "version": 1,
    "filters": {
        "only_messages": {
            "()": "calllogger.utils.OnlyMessages"
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
            "level": "DEBUG" if settings.debug else "INFO",
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
            "level": "DEBUG",
        }
    }
})
