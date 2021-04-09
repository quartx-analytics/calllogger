# Standard Lib
from queue import Queue
import threading

# Third Party
import pytest
import requests
from requests_mock import Mocker

# Local
from calllogger.api import cdr
from calllogger.record import CallDataRecord
from calllogger.conf import settings, TokenAuth


@pytest.fixture
def record():
    """Return a pre created call record."""
    record = CallDataRecord(call_type=1)
    record.number = "0876521354"
    record.line = 1
    record.ext = 102
    record.ring = 10
    record.duration = 0
    return record.data


@pytest.fixture
def api(mocker):
    # Args
    queue = Queue(10)
    running = threading.Event()
    tokenauth = TokenAuth(settings.token)
    running.set()

    # Setup worker and mock running flag so loop will only run once
    obj = cdr.CDRWorker(queue, running, tokenauth)
    mocked = mocker.patch.object(obj, "_running")
    mocked.is_set.side_effect = [True, False]
    mocker.patch.object(obj.timeout, "sleep")
    yield obj


def test_empty_queue(api, requests_mock: Mocker):
    """Test that entrypoint don't fail if queue is empty."""
    requests_mock.post(cdr.cdr_url, text="", status_code=201)
    api.entrypoint()

    assert api.queue.empty()
    assert not requests_mock.called


@pytest.mark.parametrize("status_code", [200, 201, 202, 203, 204, 205, 206, 207, 208, 226])
def test_2xx(api, record, requests_mock, status_code, mocker):
    """Test that all 2xx status codes work as expected."""
    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, json={"success": True}, status_code=status_code)
    push_spy = mocker.spy(api, "push_record")
    api.entrypoint()

    assert api.queue.empty()
    assert requests_mock.called
    assert push_spy.call_count == 1


@pytest.mark.parametrize("bad_code", [404, 408, 500, 501, 502, 503, requests.ConnectionError, requests.Timeout])
def test_retry_requests(api, record, requests_mock, mocker, bad_code):
    """Test that the request gets retried on error."""
    # This is required to allow the loop to run twice
    mocked = mocker.patch.object(api, "_running")
    mocked.is_set.side_effect = [True, True, False]

    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, response_list=[
        {"status_code": bad_code} if isinstance(bad_code, int) else {"exc": bad_code},
        {"status_code": 201, "json": {"success": True}},
    ])
    push_spy = mocker.spy(api, "push_record")
    api.entrypoint()

    assert api.queue.empty()
    assert requests_mock.called
    assert push_spy.call_count == 2


@pytest.mark.parametrize("bad_code", [400, 401])
def test_no_retry_requests(api, record, requests_mock, mocker, bad_code):
    """Test that the request"""
    # This is required to allow the loop to run twice
    mocked = mocker.patch.object(api, "_running")
    mocked.is_set.side_effect = [True, True, False]

    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, status_code=bad_code, json={"success": False})
    push_spy = mocker.spy(api, "push_record")
    api.entrypoint()

    assert api.queue.empty()
    assert requests_mock.called
    assert push_spy.call_count == 1


@pytest.mark.parametrize("bad_code", [401, 402, 403])
def test_status_quit(api, record, requests_mock, mocker, bad_code):
    """Test that the api quits for authorization failers."""
    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, status_code=bad_code, json={"success": True})
    push_spy = mocker.spy(api, "push_record")
    running_spy = mocker.spy(api.running, "clear")
    api.entrypoint()

    assert api.queue.empty()
    assert requests_mock.called
    assert push_spy.call_count == 1
    assert running_spy.called


def test_handled_exception(api, requests_mock, mocker):
    """Test that a python exception is caught and record is ignored."""
    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, exc=RuntimeError)
    push_spy = mocker.spy(api, "push_record")
    api.entrypoint()

    assert api.queue.empty()
    assert push_spy.call_count == 1


def test_unhandled_exception(api, mocker):
    api.queue.put(record)
    mocked = mocker.patch.object(api, "push_record")
    mocked.side_effect = RuntimeError
    running_spy = mocker.spy(api.running, "clear")
    with pytest.raises(RuntimeError):
        api.run()

    assert api.queue.empty()
    assert mocked.call_count == 1
    assert running_spy.called
