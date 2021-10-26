# Third Party
from urllib.parse import urlencode
from queue import Queue
import pytest
import psutil

# Local
from calllogger.api import influx
from calllogger.telemetry import InfluxCollector, collector


@pytest.fixture
def new_collector():
    """Create a new collector when required."""
    return InfluxCollector(
        collector.org,
        collector.bucket,
    )


@pytest.fixture
def api(new_collector, disable_sleep):
    # Setup worker and mock running flag so loop will only run once
    obj = influx.InfluxWrite("https://fake.url", new_collector, "fake_token")
    disable_sleep.side_effect = [False, True]
    yield obj


# noinspection PyUnusedLocal
def test_success(api: influx.InfluxWrite, mocker, requests_mock):
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


# noinspection PyUnusedLocal
def test_quit(api: influx.InfluxWrite, mocker, requests_mock):
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


def test_defaults(new_collector):
    """Test that default_fields & default_tags get added to the collector."""
    default_fields = {"field": "value"}
    default_tags = {"tag": "value"}

    influx.InfluxWrite(
        "https://fake.url",
        new_collector,
        "fake_token",
        default_tags=default_tags,
        default_fields=default_fields,
    )

    assert new_collector.default_tags == default_tags
    assert new_collector.default_fields == default_fields
