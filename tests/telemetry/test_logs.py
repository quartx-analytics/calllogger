# Standard Lib
import socket
import threading

# Local
from calllogger.telemetry import logs
from calllogger import closeers


def test_setup_remote_logs(mocker):
    """Test that fluent logging works without raising an error."""
    mocker.patch.object(socket.socket, "connect_ex", return_value=0)
    spy_formatter = mocker.spy(logs, "FluentRecordFormatter")
    spy_handler = mocker.spy(logs, "FluentHandler")
    current_closers = len(closeers)
    logs.setup_remote_logs("user")

    # There should be 1 extra close object registered
    assert len(closeers) == current_closers + 1
    assert spy_handler.called
    assert spy_formatter.called


def test_setup_remote_logs_socket_fail(mocker):
    """Test that fluent logging works without raising an error."""
    mocker.patch.object(socket.socket, "connect_ex", return_value=1)
    mocked_timer = mocker.patch.object(threading, "Timer")
    spy_formatter = mocker.spy(logs, "FluentRecordFormatter")
    spy_handler = mocker.spy(logs, "FluentHandler")
    current_closers = len(closeers)
    logs.setup_remote_logs("user")

    # There should be no new close object registered
    assert len(closeers) == current_closers
    assert mocked_timer.called
    assert not spy_handler.called
    assert not spy_formatter.called


def test_setup_remote_logs_no_retry(mocker):
    """Test that the thread timer dose not get called if we have it max retry."""
    mocker.patch.object(socket.socket, "connect_ex", return_value=1)
    mocked_timer = mocker.patch.object(threading, "Timer")
    spy_formatter = mocker.spy(logs, "FluentRecordFormatter")
    spy_handler = mocker.spy(logs, "FluentHandler")
    logs.setup_remote_logs("user", retry=5)

    assert not mocked_timer.called
    assert not spy_handler.called
    assert not spy_formatter.called
