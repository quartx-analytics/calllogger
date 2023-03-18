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

__all__ = ["__version__", "stopped", "settings", "closeers"]

# Standard lib
import logging.config

# Third Party
import sentry_sdk
from decouple import config
from sentry_sdk.integrations.threading import ThreadingIntegration

# Local
from calllogger import conf, utils

__version__ = "2.0.0"

# Setup Sentry
sentry_sdk.init(
    config("SENTRY_DSN", default="", cast=conf.b64),
    release=__version__,
    environment=config("ENVIRONMENT", default="Testing", cast=str),
    integrations=[ThreadingIntegration(propagate_hub=True)],
    max_breadcrumbs=25,
)

# Initialize Settings
stopped = utils.ExitCodeEvent()
settings = conf.Settings()
closeers: list[callable] = []

# Logging configuration
logging_config = {
    "version": 1,
    "filters": {"only_messages": {"()": "calllogger.utils.OnlyMessages"}},
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
            "level": "DEBUG",
        },
        "console_errors": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "levelname",
            "level": "WARNING",
        },
    },
    "loggers": {
        "calllogger": {
            "handlers": ["console_messages", "console_errors"],
            "level": "DEBUG" if settings.debug else "INFO",
        }
    },
}

# Apply logging config
logging.config.dictConfig(logging_config)
