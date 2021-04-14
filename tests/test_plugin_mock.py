# Standard Lib
import random
import time

# Third Party
import pytest

# Local
from calllogger.plugins import MockCalls
from .utils import call_plugin

TRANSFER_YES = 0
TRANSFER_NO = 1
OUTGOING = 0
RECEIVED = 1


@pytest.fixture
def mock_plugin(mocker):
    plugin = call_plugin(MockCalls)
    mocked_runner = mocker.patch.object(plugin, "_running")
    mocked_runner.is_set.side_effect = [True, False]
    mocker.patch.object(time, "sleep")
    yield plugin


@pytest.mark.parametrize("sleep", [False, True])
@pytest.mark.parametrize("direction", [OUTGOING, RECEIVED])
@pytest.mark.parametrize("transfer", [TRANSFER_YES, TRANSFER_NO])
def test_basic_useage(mock_plugin: MockCalls, mocker, transfer, direction, sleep):
    """Test that all sorts of mocked call types work and so not raise an exception."""
    # Change direction param to force select outgoing
    mocker.patch.object(random, "randrange", return_value=transfer)
    mock_plugin.direction = direction  # Force direction
    mock_plugin.sleep = sleep  # Force direction
    mock_plugin.run()
