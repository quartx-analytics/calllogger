# Standard Lib
from queue import Queue

# Third Party
import pytest
from requests_mock import Mocker

# Local
from calllogger.api import cdr
from calllogger.record import CallDataRecord
from calllogger.conf import TokenAuth
from calllogger import running


@pytest.fixture
def record():
    """Return a pre created call record."""
    record = CallDataRecord(call_type=1)
    record.number = "0876521354"
    record.line = 1
    record.ext = 102
    record.ring = 10
    record.duration = 0
    return record.__dict__


@pytest.fixture
def api(mocker):
    queue = Queue(10)
    tokenauth = TokenAuth("token")

    # Setup worker and mock running flag so loop will only run once
    obj = cdr.CDRWorker(queue, tokenauth)
    mocked = mocker.patch.object(running, "is_set")
    mocked.side_effect = [True, True, False]
    mocker.patch.object(obj.timeout, "sleep")
    yield obj


def test_empty_queue(api, requests_mock: Mocker):
    """Test that entrypoint don't fail if queue is empty."""
    requests_mock.post(cdr.cdr_url, text="", status_code=201)
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

    requests_mock.post(cdr.cdr_url, json={"success": True}, status_code=400)
    request_spy = mocker.spy(api, "_send_request")
    success = api.run()

    assert not success
    assert api.queue.empty()
    assert requests_mock.called
    assert request_spy.call_count == 1
