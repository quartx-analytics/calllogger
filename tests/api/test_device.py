# Local
import pytest

from calllogger.api import device

mock_identifier = "0A:B3:FF:C3:EF:00"
mock_token = "s3d4f56s6ad7f678w8e87"


def test_success(requests_mock, mock_running):
    expected_resp = {"token": mock_token}
    mocked_request = requests_mock.post(device.linking_url, status_code=201, json=expected_resp)
    resp = device.link_device(mock_identifier)

    assert mock_running.called
    assert mocked_request.called
    assert resp == mock_token


def test_retry(requests_mock, mock_running, disable_sleep):
    expected_resp = {"token": mock_token}
    mocked_request = requests_mock.post(device.linking_url, response_list=[
        {"status_code": 204},
        {"status_code": 201, "json": expected_resp},
    ])
    resp = device.link_device(mock_identifier)

    assert disable_sleep.called
    assert mock_running.called
    assert mocked_request.call_count == 2
    assert resp == mock_token


def test_unexpected_status(requests_mock, mock_running):
    mocked_request = requests_mock.post(device.linking_url, status_code=202)
    resp = device.link_device(mock_identifier)

    assert mock_running.called
    assert mocked_request.called
    assert resp is None


def test_errored(requests_mock, mock_running, disable_sleep):
    mocked_request = requests_mock.post(device.linking_url, exc=RuntimeError)
    with pytest.raises(RuntimeError):
        device.link_device(mock_identifier)

    assert disable_sleep.called
    assert mock_running.called
    assert mocked_request.called
