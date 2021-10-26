# Third Party
import pytest

# Local
from calllogger.plugins.internal import mockcalls
from ..common import call_plugin
from calllogger import stopped

TRANSFER_NO = 0
TRANSFER_YES = 1
TRANSFER_INT = 0
TRANSFER_EXT = 1
OUTGOING = 0
RECEIVED = 1


@pytest.fixture
def mock_plugin(mocker, disable_sleep):
    plugin = call_plugin(mockcalls.MockCalls)
    mocked_runner = mocker.patch.object(stopped, "is_set")
    mocked_runner.side_effect = [False, True]
    plugin.exts = 3  # Limit extensions
    yield plugin


@pytest.mark.parametrize("sleep", [False, True])
@pytest.mark.parametrize("transferred_direction", [TRANSFER_INT, TRANSFER_EXT])
@pytest.mark.parametrize("transfer", [TRANSFER_NO, TRANSFER_YES])
@pytest.mark.parametrize("direction", [OUTGOING, RECEIVED])
def test_basic_useage(mock_plugin: mockcalls.MockCalls, mocker, direction, transfer, transferred_direction, sleep):
    """Test that all sorts of mocked call types work and DO not raise an exception."""
    mock_plugin.transferred_direction = transferred_direction
    mock_plugin.transferred_chance = transfer
    mock_plugin.direction = direction
    mock_plugin.sleep = sleep

    spy_transfered = mocker.spy(mock_plugin, "transfered_call")
    spy_outgoing = mocker.spy(mock_plugin, "outgoing")
    spy_received = mocker.spy(mock_plugin, "received")
    successful = mock_plugin.run()

    assert successful
    assert spy_transfered.called == transfer
    assert (spy_received.called if direction else spy_outgoing.called) is True
