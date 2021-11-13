# Local
from calllogger.telemetry import logs


def test_send_logs_to_logzio(mocker):
    """Test that fluent logging works without raising an error."""
    spy_logger = mocker.spy(logs.logger, "addHandler")
    mocked_logz = mocker.patch.object(logs, "ExtraLogzioHandler")
    logs.send_logs_to_logzio(
        url="https://fake.url",
        token="fake_token",
        extras={
            "identifier": "CB:BB:27:BF:51:5C"
        }
    )

    # There should be 1 extra close object registered
    assert mocked_logz.called
    assert spy_logger.called
