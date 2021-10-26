# Local
import pytest

from calllogger.api import device

mock_identifier = "0A:B3:FF:C3:EF:00"
mock_token = "s3d4f56s6ad7f678w8e87"


def test_success(requests_mock):
    expected_resp = {"token": mock_token}
    mocked_request = requests_mock.post(device.linking_url, status_code=201, json=expected_resp)
    resp = device.link_device(mock_identifier)

    assert mocked_request.called
    assert resp == mock_token


@pytest.mark.parametrize("timeout", [60, -1])
def test_retry(requests_mock, disable_sleep, timeout, mock_settings):
    expected_resp = {"token": mock_token}
    mock_settings(device_reg_timeout=timeout)
    mocked_request = requests_mock.post(device.linking_url, response_list=[
        {"status_code": 204},
        {"status_code": 201, "json": expected_resp},
    ])

    device.link_device(mock_identifier)
    assert disable_sleep.called
    assert mocked_request.call_count == (2 if timeout > 0 else 1)


def test_unexpected_status(requests_mock):
    mocked_request = requests_mock.post(device.linking_url, status_code=202)
    resp = device.link_device(mock_identifier)

    assert mocked_request.called
    assert resp is None


def test_errored(requests_mock, disable_sleep):
    mocked_request = requests_mock.post(device.linking_url, exc=RuntimeError)
    with pytest.raises(RuntimeError):
        device.link_device(mock_identifier)

    assert disable_sleep.called
    assert mocked_request.called
