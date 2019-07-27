import pytest
from unittest import mock
from quartx_call_logger.api import API, url
from quartx_call_logger.record import Record
import requests
import queue


@pytest.fixture
def api():
    obj = API()
    obj.timeout = 0.01
    with mock.patch.object(obj, "running") as mocker:
        mocker.is_set.side_effect = [True, False]
        yield obj


@pytest.fixture
def record():
    return Record(1, number="0876521354", line=1, ext=102, ring=10, duration=0)


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
    api.push(record)
    assert not api.queue.empty()


def test_empty_queue(api, requests_mock, req_callback):
    assert api.queue.empty()
    requests_mock.post(url, text=req_callback.resp(""), status_code=201)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is False


def test_run_201(api, record, requests_mock, req_callback):
    api.push(record)
    requests_mock.post(url, json=req_callback.resp({"success": True}), status_code=201)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_400(api, record, requests_mock, req_callback):
    api.push(record)
    requests_mock.post(url, json=req_callback.resp({"error": "field is missing"}), status_code=400)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_401(api, record, requests_mock, req_callback):
    api.push(record)
    requests_mock.post(url, json=req_callback.resp({"error": "permission required"}), status_code=401)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_403(api, record, requests_mock, req_callback):
    api.push(record)
    requests_mock.post(url, json=req_callback.resp({"error": "access forbidden"}), status_code=403)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_run_500(api, record, requests_mock, req_callback):
    api.push(record)
    requests_mock.post(url, text=req_callback.resp(""), status_code=500)
    api.run()

    assert api.queue.empty()
    assert req_callback.called is True


def test_exception_timeout(api, record):
    api.push(record)
    with mock.patch.object(api, "session") as mocker:
        mocker.post.side_effect = requests.Timeout
        api.run()
        mocker.post.assert_called()


def test_exception_connection_error(api, record):
    api.push(record)
    with mock.patch.object(api, "session") as mocker:
        mocker.post.side_effect = requests.ConnectionError
        api.run()
        mocker.post.assert_called()


def test_exception_connection_error_incoming(api):
    record = Record(0, number="0876521354", line=1, ext=102)
    api.push(record)
    with mock.patch.object(api, "session") as mocker:
        mocker.post.side_effect = requests.ConnectionError
        api.run()
        mocker.post.assert_called()


def test_exception_queue_full(api, record):
    with mock.patch.object(api, "queue", spec=True) as queue_mock:
        queue_mock.put_nowait.side_effect = queue.Full
        api.push(record)

        with mock.patch.object(api, "session") as req_mock:
            req_mock.post.side_effect = requests.Timeout
            api.run()
            req_mock.post.assert_called()
