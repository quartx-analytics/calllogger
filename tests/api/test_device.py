# Local
from calllogger.api import device
from calllogger import running

mock_identifier = "0A:B3:FF:C3:EF:00"
mock_token = "s3d4f56s6ad7f678w8e87"


def test_link_device_success(requests_mock, mocker):
    mocked = mocker.patch.object(running, "is_set")
    mocked.return_value = True

    expected_resp = {"token": mock_token}
    mocked_request = requests_mock.post(device.linking_url, status_code=201, json=expected_resp)
    resp = device.link_device(mock_identifier)

    assert mocked_request.called
    assert resp == mock_token
