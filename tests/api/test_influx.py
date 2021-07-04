# Third Party
import pytest
import psutil

# Local
from calllogger.api import influx
from calllogger.metrics import collector


@pytest.fixture
def api(mocker):
    # Setup worker and mock running flag so loop will only run once
    obj = influx.InfluxWrite(collector, "fake_token")
    mocker.patch.object(influx, "sleeper", side_effect=[True, False])
    yield obj


def test_something(api, mocker, requests_mock):
    requests_mock.post(collector.url, status_code=204)
    mocker.patch.object(psutil, "cpu_percent", return_value=1.5)
    mocker.patch.object(api._process, "cpu_percent", return_value=1.5)
    api.run()
