# Local
from calllogger.telemetry.logs import setup_remote_logs
from calllogger import closeers


def test_setup_remote_logs():
    """Test that fluent logging works with raising an error."""
    current_closers = len(closeers)
    setup_remote_logs("user")

    # There is not much we can test for here
    assert len(closeers) == current_closers + 1
