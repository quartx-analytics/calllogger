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


# @pytest.mark.parametrize("sleep", [False, True])
# @pytest.mark.parametrize("transferred_direction", [TRANSFER_INT, TRANSFER_EXT])
# @pytest.mark.parametrize("transfer", [TRANSFER_NO, TRANSFER_YES])
# @pytest.mark.parametrize("direction", [OUTGOING, RECEIVED])
def test_basic_useage(mock_plugin: MockCalls, mocker):#, direction, transfer, transferred_direction, sleep):
    """Test that all sorts of mocked call types work and DO not raise an exception."""
    mock_plugin.transferred_direction = 1
    mock_plugin.transferred_chance = 1
    mock_plugin.direction = 1
    mock_plugin.sleep = 1

    spy_transfered = mocker.spy(mock_plugin, "transfered_call")
    mock_plugin.run()

    assert spy_transfered.called == 1
