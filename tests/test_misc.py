# Standard lib
from importlib.metadata import version
import os

# Local
from calllogger import __version__ as source_ver

# Third Party
import pytest


@pytest.mark.skipif(os.environ.get("tox") != "true", reason="Test will only work in a tox environment.")
def test_version():
    """
    Test that the version number in the
    source matches up with the package version.
    """
    package_ver = version("calllogger")
    assert package_ver == source_ver
