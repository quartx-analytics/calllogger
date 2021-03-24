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
    assert requests_mock.called is True
    assert push_spy.call_count == 1


@pytest.mark.parametrize("bad_code", [404, 408, 500, 501, 502, 503])
def test_retry_requests(api, record, requests_mock, bad_code, mocker):
    """Test that the request"""
    # This is required to allow the loop to run twice
    mocked = mocker.patch.object(api, "_running")
    mocked.is_set.side_effect = [True, True, False]

    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, response_list=[
        {"status_code": bad_code, "json": {"error": "field is missing"}},
        {"status_code": 201, "json": {"success": True}},
    ])
    push_spy = mocker.spy(api, "push_record")
    api.entrypoint()

    assert api.queue.empty()
    assert requests_mock.called is True
    assert push_spy.call_count == 2


@pytest.mark.parametrize("exc", [requests.ConnectionError, requests.Timeout])
def test_connection_errors(api, record, requests_mock, exc, mocker):
    """Test that the request"""
    # This is required to allow the loop to run twice
    mocked = mocker.patch.object(api, "_running")
    mocked.is_set.side_effect = [True, True, False]

    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, response_list=[
        {"exc": exc},
        {"status_code": 201, "json": {"success": True}},
    ])
    push_spy = mocker.spy(api, "push_record")
    api.entrypoint()

    assert api.queue.empty()
    assert requests_mock.called is True
    assert push_spy.call_count == 2


# def test_run_401(api, record, requests_mock):
#     api.queue.put(record)
#     requests_mock.post(cdr.cdr_url, json={"error": "permission required"}, status_code=401)
#     api.entrypoint()
#
#     assert api.queue.empty()
#     assert requests_mock.called is True
#
#
# def test_run_403(api, record, requests_mock):
#     api.queue.put(record)
#     requests_mock.post(cdr.cdr_url, json={"error": "access forbidden"}, status_code=403)
#     api.entrypoint()
#
#     assert api.queue.empty()
#     assert requests_mock.called is True
#
#
# def test_run_500(api, record, requests_mock):
#     api.queue.put(record)
#     requests_mock.post(cdr.cdr_url, text="", status_code=500)
#     api.entrypoint()
#
#     assert not api.queue.empty()
#     assert requests_mock.called is True
#
#
# def test_exception_timeout(api, record):
#     api.queue.put(record)
#     with mock.patch.object(api, "session") as mocker:
#         mocker.post.side_effect = requests.Timeout
#         api.run()
#         mocker.post.assert_called()
#
#
# def test_exception_connection_error(api, record):
#     api.queue.put(record)
#     with mock.patch.object(api, "session") as mocker:
#         mocker.post.side_effect = requests.ConnectionError
#         api.run()
#         mocker.post.assert_called()
#
#
# def test_exception_connection_error_incoming(api):
#     record = CallDataRecord(call_type=0, number="0876521354", line=1, ext=102)
#     api.queue.put(record)
#     with mock.patch.object(api, "session") as mocker:
#         mocker.post.side_effect = requests.ConnectionError
#         api.entrypoint()
#         mocker.post.assert_called()
#
#
# def test_exception_queue_full(api, record):
#     with mock.patch.object(api, "queue", spec=True) as queue_mock:
#         queue_mock.put_nowait.side_effect = queue.Full
#         api.queue.put(record)
#
#         with mock.patch.object(api, "session") as req_mock:
#             req_mock.post.side_effect = requests.Timeout
#             api.entrypoint()
#             req_mock.post.assert_called()
