# Local
from calllogger.plugins import find_plugins
from calllogger.plugins import MockCalls

internal_plugins = [MockCalls]


def test_find_plugins():
    """Test that all the internal plugins get installed."""
    plugins = find_plugins()
    for internal in internal_plugins:
        name = internal.__name__.lower()
        assert name in plugins
        plugins.pop(name)

    # Now that all internal plugins have been removed
    # the plugin dict should be empty
    assert len(plugins) == 0
