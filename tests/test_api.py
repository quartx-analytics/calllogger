import pytest
from unittest import mock
from quartx_call_logger.api import API
from quartx_call_logger.record import Record
from quartx_call_logger import settings
from urllib import parse as urlparse
import threading
import requests
import queue


@pytest.fixture
def url():
    return urlparse.urlunsplit((
        "https" if settings.SSL else "http",  # scheme
        settings.DOMAIN,  # netloc
        "/monitor/cdr/record/",  # path,
        "",  # query
        "",  # fragment
    ))


@pytest.fixture
def api():
    running = threading.Event()
    obj = API(queue.Queue(10), running)
    obj.timeout = 0.01
    with mock.patch.object(obj, "running") as mocker:
        mocker.is_set.side_effect = [True, False]
        yield obj


@pytest.fixture
def record():
    return Record(call_type=1, number="0876521354", line=1, ext=102, ring=10, duration=0)


@pytest.fixture
def req_callback():
    class Called:
        def __init__(self):
            self.called = False

        def resp(self, resp):
            def callback(request, context):
                req_data = request.json()
                for field in ["call_type", "number", "line", "ext", "ring", "duration"]:
                    assert field in req_data
                self.called = True
                return resp
            return callback
    return Called()


def test_push(api, record):
    assert api.queue.empty()
    api.queue.put(record)
    assert not api.queue.empty()


def test_empty_queue(url, api, requests_mock, req_callback):
    assert api.queue.empty()
    requests_mock.post(url, text=req_callback.resp(""), status_code=201)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is False


def test_run_201(url, api, record, requests_mock, req_callback):
    api.queue.put(record)
    requests_mock.post(url, json=req_callback.resp({"success": True}), status_code=201)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_400(url, api, record, requests_mock, req_callback):
    api.queue.put(record)
    requests_mock.post(url, json=req_callback.resp({"error": "field is missing"}), status_code=400)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_401(url, api, record, requests_mock, req_callback):
    api.queue.put(record)
    requests_mock.post(url, json=req_callback.resp({"error": "permission required"}), status_code=401)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_403(url, api, record, requests_mock, req_callback):
    api.queue.put(record)
    requests_mock.post(url, json=req_callback.resp({"error": "access forbidden"}), status_code=403)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_500(url, api, record, requests_mock, req_callback):
    api.queue.put(record)
    requests_mock.post(url, text=req_callback.resp(""), status_code=500)
    api.run()

    assert not api.queue.empty()
    assert req_callback.called is True


def test_exception_timeout(api, record):
    api.queue.put(record)
    with mock.patch.object(api, "session") as mocker:
        mocker.post.side_effect = requests.Timeout
        api.run()
        mocker.post.assert_called()


def test_exception_connection_error(api, record):
    api.queue.put(record)
    with mock.patch.object(api, "session") as mocker:
        mocker.post.side_effect = requests.ConnectionError
        api.run()
        mocker.post.assert_called()


def test_exception_connection_error_incoming(api):
    record = Record(call_type=0, number="0876521354", line=1, ext=102)
    api.queue.put(record)
    with mock.patch.object(api, "session") as mocker:
        mocker.post.side_effect = requests.ConnectionError
        api.run()
        mocker.post.assert_called()


def test_exception_queue_full(api, record):
    with mock.patch.object(api, "queue", spec=True) as queue_mock:
        queue_mock.put_nowait.side_effect = queue.Full
        api.queue.put(record)

        with mock.patch.object(api, "session") as req_mock:
            req_mock.post.side_effect = requests.Timeout
            api.run()
            req_mock.post.assert_called()
