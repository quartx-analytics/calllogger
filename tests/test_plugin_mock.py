# Standard Lib
import random
import time

# Third Party
import pytest

# Local
from calllogger.plugins import MockCalls
from .utils import call_plugin

TRANSFER_NO = 0
TRANSFER_YES = 1
TRANSFER_INT = 0
TRANSFER_EXT = 1
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
@pytest.mark.parametrize("transferred_direction", [TRANSFER_INT, TRANSFER_EXT])
@pytest.mark.parametrize("transfer", [TRANSFER_YES, TRANSFER_NO])
@pytest.mark.parametrize("direction", [OUTGOING, RECEIVED])
def test_basic_useage(mock_plugin: MockCalls, direction, transfer, transferred_direction, sleep):
    """Test that all sorts of mocked call types work and DO not raise an exception."""
    mock_plugin.transferred_direction = transferred_direction
    mock_plugin.transferred_chance = transfer
    mock_plugin.direction = direction
    mock_plugin.sleep = sleep
    mock_plugin.run()
