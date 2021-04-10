# Third Party
import requests

# Local
from calllogger.api import handlers


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
