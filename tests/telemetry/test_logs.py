# Standard Lib
import socket

# Local
from calllogger.telemetry.logs import setup_remote_logs
from calllogger import closeers


def test_setup_remote_logs(mocker):
    """Test that fluent logging works without raising an error."""
    mocker.patch.object(socket.socket, "connect_ex", return_value=0)
    current_closers = len(closeers)
    setup_remote_logs("user")

    # There should be 1 extra close object registered
    assert len(closeers) == current_closers + 1


def test_setup_remote_logs_socket_fail(mocker):
    """Test that fluent logging works without raising an error."""
    mocker.patch.object(socket.socket, "connect_ex", return_value=1)
    current_closers = len(closeers)
    setup_remote_logs("user")

    # There should be no new close object registered
    assert len(closeers) == current_closers
