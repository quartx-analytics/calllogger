# Third Party
from urllib.parse import urlencode
from queue import Queue
import pytest
import psutil

# Local
from calllogger.api import influx
from calllogger.telemetry import collector


@pytest.fixture
def api(mocker):
    # Setup worker and mock running flag so loop will only run once
    obj = influx.InfluxWrite(collector, "fake_token")
    mocker.patch.object(influx, "sleeper", side_effect=[True, False])
    yield obj


# noinspection PyUnusedLocal
def test_success(api: influx.InfluxWrite, mocker, requests_mock, mock_running):
    # Mock the influx API request
    mocked_req = requests_mock.post(
        f"{api.request.url}?{urlencode(api.request.params)}",
        status_code=204,
    )

    # Mock the CPU usage calls, stops it from slowing down tests
    mocker.patch.object(psutil, "cpu_percent", return_value=1.5)
    mocker.patch.object(api._process, "cpu_percent", return_value=1.5)
    api.run()

    assert mocked_req.called
    # There should be 1 metric left as this is created after the request
    assert api.collector.queue.qsize() == 1


# noinspection PyUnusedLocal
def test_quit(api: influx.InfluxWrite, mocker, requests_mock, mock_running):
    # Mock the influx API request
    mocked_req = requests_mock.post(
        f"{api.request.url}?{urlencode(api.request.params)}",
        status_code=401,
    )

    # Mock the CPU usage calls, stops it from slowing down tests
    mocker.patch.object(psutil, "cpu_percent", return_value=1.5)
    mocker.patch.object(api._process, "cpu_percent", return_value=1.5)

    assert api.quit is False
    api.run()
    assert mocked_req.called
    assert api.quit is True


def test_no_metrics(api: influx.InfluxWrite, mocker, requests_mock):
    # Mock the influx API request
    mocked_req = requests_mock.post(
        f"{api.request.url}?{urlencode(api.request.params)}",
        status_code=204,
    )

    # Replace collector queue with an empty queue
    mocker.patch.object(api.collector, "queue", new_callable=Queue)

    # Mock the CPU usage calls, stops it from slowing down tests
    api.submit_metrics()

    assert not mocked_req.called
    # There should be 1 metric left as this is created after the request
    assert api.collector.queue.empty()
