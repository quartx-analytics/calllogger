# Standard Lib
import time

# Third Party
import pytest

# Local
from calllogger.plugins import MockCalls
from .utils import call_plugin


@pytest.fixture
def mock_plugin(mocker):
    plugin = call_plugin(MockCalls)
    mocked_runner = mocker.patch.object(plugin, "_running")
    mocked_runner.is_set.side_effect = [True, False]
    mocker.patch.object(time, "sleep")
    yield plugin


def test_outgoing(mock_plugin: MockCalls):
    # Change direction param to force select outgoing
    mock_plugin.direction = 0
    mock_plugin.run()


def test_outgoing_transferred(mock_plugin: MockCalls):
    # Change direction param to force select outgoing
    mock_plugin.transferred_chance = 0
    mock_plugin.direction = 0
    mock_plugin.run()
