# Standard lib
import json

# Third Party
import requests
import pytest

# Local
from calllogger.api import handlers, info
from calllogger.secrets import TokenAuth
from calllogger import running

test_url = "https://testing.test/test"
client_error_status = [
    (400, False),
    (401, True),
    (402, True),
    (403, True)
]


@pytest.fixture
def api(mocker):
    obj = handlers.QuartxAPIHandler()
    mocked = mocker.patch.object(running, "is_set")
    mocked.side_effect = [True, False]
    mocker.patch.object(obj.timeout, "sleep")
    yield obj


def test_decode_response_json():
    """Test that decode_response returns a full json object."""
    resp = requests.Response()
    resp.encoding = "utf8"
    resp._content = b'{"test": true}'

    # We set limit to 2 here to make sure it has no effect
    data = handlers.decode_response(resp, limit=2)
    assert data == {"test": True}


def test_decode_response_text():
    """Test that decode_response returns a text with a length limit of 13."""
    resp = requests.Response()
    resp.encoding = "utf8"
    resp._content = b'testdata-testdata-testdata'

    # We use 13 only for testing, normally it's 1,000
    data = handlers.decode_response(resp, limit=13)
    assert data == "testdata-test"
    assert len(data) == 13


@pytest.mark.parametrize("status_code", [200, 201, 202, 203, 204, 205, 206, 207, 208, 226])
def test_ok_requests(api, requests_mock, status_code, mocker):
    """Test that all 2xx status codes work as expected."""
    requests_mock.get(test_url, json={"success": True}, status_code=status_code)
    request_spy = mocker.spy(api, "_send_request")
    resp = api.make_request(method="GET", url=test_url)

    assert resp.json() == {"success": True}
    assert requests_mock.called
    assert request_spy.call_count == 1


@pytest.mark.parametrize("bad_code", [404, 408, 500, 501, 502, 503, requests.ConnectionError, requests.Timeout])
def test_server_network_errors(api, requests_mock, mocker, bad_code):
    """Test for server/network errors that can be retried."""
    mocked = mocker.patch.object(running, "is_set")
    mocked.side_effect = [True, True, False]
    request_spy = mocker.spy(api, "_send_request")

    requests_mock.get(test_url, response_list=[
        {"status_code": bad_code} if isinstance(bad_code, int) else {"exc": bad_code},
        {"status_code": 201, "json": {"success": True}},
    ])
    resp = api.make_request(method="GET", url=test_url)

    assert resp.json() == {"success": True}
    assert requests_mock.called
    assert request_spy.call_count == 2


def test_retry_with_break(api, requests_mock, mocker):
    """Test for server/network errors that can be retried."""
    mocked = mocker.patch.object(running, "is_set")
    mocked.side_effect = [True, False]
    request_spy = mocker.spy(api, "_send_request")
    api.suppress_errors = True

    requests_mock.get(test_url, response_list=[
        {"status_code": 500},
        {"status_code": 201, "json": {"success": True}},
    ])
    resp = api.make_request(method="GET", url=test_url)

    assert not resp
    assert requests_mock.called
    assert request_spy.call_count == 1


def client_errors(api, requests_mock, mocker, bad_code, cleard):
    mocked = mocker.patch.object(running, "is_set")
    mocked.side_effect = [True, False]
    clear_spy = mocker.spy(running, "clear")
    request_spy = mocker.spy(api, "_send_request")
    requests_mock.get(test_url, status_code=bad_code, json={"success": False})
    resp = api.make_request(method="GET", url=test_url)

    assert requests_mock.called
    assert request_spy.call_count == 1
    assert clear_spy.called is cleard
    return resp


@pytest.mark.parametrize("bad_code,cleard", client_error_status)
def test_client_errors(api, requests_mock, mocker, bad_code, cleard):
    """Test for client errors. Errors that can not be retried."""
    with pytest.raises(requests.HTTPError):
        client_errors(api, requests_mock, mocker, bad_code, cleard)


@pytest.mark.parametrize("bad_code,cleard", client_error_status)
def test_client_errors_suppressed(api, requests_mock, mocker, bad_code, cleard):
    """Test for client errors. Errors that can not be retried."""
    api.suppress_errors = True
    resp = client_errors(api, requests_mock, mocker, bad_code, cleard)
    assert resp is False


@pytest.mark.parametrize("error", [RuntimeError, json.JSONDecodeError, TypeError])
def test_unexpected_errors(api, mocker, error):
    mocked = mocker.patch.object(api.session, "send")
    mocked.side_effect = RuntimeError

    with pytest.raises(RuntimeError):
        api.make_request(method="GET", url=test_url)
    assert mocked.call_count == 1


def test_get_owner_info(requests_mock, mocker):
    tokenauth = TokenAuth("token")
    mocked = mocker.patch.object(running, "is_set")
    mocked.return_value = True
    expected_resp = {'id': 1, 'name': 'Test', 'email': 'test@test.com'}
    mocked_request = requests_mock.get(info.info_url, status_code=200, json=expected_resp)
    resp = info.get_owner_info(tokenauth)

    assert mocked_request.called
    assert resp == expected_resp
