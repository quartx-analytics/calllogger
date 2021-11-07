# Standard Lib
from queue import SimpleQueue, Empty

# Third Party
import pytest
from requests_mock import Mocker

# Local
from calllogger.api import cdr
from calllogger.record import CallDataRecord
from calllogger.utils import TokenAuth
from calllogger import stopped


@pytest.fixture
def record():
    """Return a pre created call record."""
    record = CallDataRecord(call_type=1)
    record.number = "0876521354"
    record.line = 1
    record.ext = 102
    record.ring = 10
    record.duration = 0
    return record


@pytest.fixture
def api(mocker, disable_sleep):
    queue = SimpleQueue()
    tokenauth = TokenAuth("token")

    # Setup worker and mock running flag so loop will only run once
    obj = cdr.CDRWorker(queue, tokenauth)
    mocked = mocker.patch.object(stopped, "is_set")
    mocked.side_effect = [False, False, True]
    yield obj


def test_empty_queue(api, requests_mock: Mocker):
    """Test that entrypoint don't fail if queue is empty."""
    requests_mock.post(cdr.cdr_url, text="", status_code=204)
    api.run()

    assert api.queue.empty()
    assert not requests_mock.called


@pytest.mark.parametrize("status_code", [200, 400])
def test_ok_with_errors_suppressed(api, record, requests_mock, mocker, status_code):
    """Test that all 2xx status codes work as expected."""
    api.queue.put(record)
    requests_mock.post(cdr.cdr_url, json={"success": True}, status_code=status_code)
    request_spy = mocker.spy(api, "_send_request")
    success = api.run()

    assert success
    assert api.queue.empty()
    assert requests_mock.called
    assert request_spy.call_count == 1


def test_errors_not_suppressed(api, record, requests_mock, mocker):
    """Test that all 2xx status codes work as expected."""
    api.suppress_errors = False
    api.queue.put(record)

    requests_mock.post(cdr.cdr_url, status_code=400)
    request_spy = mocker.spy(api, "_send_request")
    success = api.run()

    assert not success
    assert api.queue.empty()
    assert requests_mock.called
    assert request_spy.call_count == 1


def test_backlogged_queue(api: cdr.CDRWorker, requests_mock: Mocker, mocker):
    """Test that entrypoint don't fail if queue is empty."""
    mocked = mocker.patch.object(api, "queue")
    mocked.qsize.return_value = 50

    def create_record(*_, **__):
        mocked.qsize.return_value -= 1
        return CallDataRecord(1)

    mocked.get.side_effect = create_record
    requests_mock.post(cdr.cdr_url, status_code=204)
    api.run()

    assert requests_mock.called


def test_backlogged_empty(api: cdr.CDRWorker, requests_mock: Mocker, mocker):
    """Test that entrypoint don't fail if queue is empty."""
    mocked = mocker.patch.object(api, "queue")
    mocked.qsize.return_value = 26
    tracker = 0

    def create_record(*_, **__):
        mocked.qsize.return_value -= 1
        nonlocal tracker
        tracker += 1
        if tracker == 10:
            raise Empty()
        else:
            return CallDataRecord(0)

    mocked.get.side_effect = create_record
    requests_mock.post(cdr.cdr_url, status_code=204)
    api.run()

    assert not requests_mock.called
