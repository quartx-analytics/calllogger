"""
MIT License

Copyright (c) 2019 QuartX

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

# Standard library
import logging
import sys

# Package
from call_logger.config import compile_settings

__all__ = ["settings"]


class CusstomStreamHandler(logging.StreamHandler):
    """
    A handler class which writes logging records, appropriately formatted, to a stream.
    Debug & Info records will be logged to sys.stdout, and all other records will be logged to sys.stderr.
    """

    # noinspection PyBroadException
    def emit(self, record):
        """Swap out the stderr stream with stdout if log level is DEBUG or INFO."""
        if record.levelno <= 20:
            org_stream = self.stream
            self.stream = sys.stdout
            try:
                super(CusstomStreamHandler, self).emit(record)
            finally:
                self.stream = org_stream
        else:
            super(CusstomStreamHandler, self).emit(record)


# Configure the logging
cli_handler = CusstomStreamHandler()
cli_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
cli_handler.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(cli_handler)
logger.setLevel(logging.DEBUG)

# The global call logger settings
settings = compile_settings()
