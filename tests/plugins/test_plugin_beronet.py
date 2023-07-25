# Third Party
import pytest

# Local
from calllogger.plugins.internal import beronet
from calllogger.record import CallDataRecord
from ..common import call_plugin
from calllogger import stopped


# id 18 = Outgoing
# id 19 = Received
good_lines = b"""
CDR,18,ISDN:1:1,SIP,100,013231111,100 <sip:02642102@sip.iptel.co>,<sip:013231111@sip.iptel.co>,23/07/21-22:39:38,23/07/21-22:40:10,23/07/21-22:39:53,23/07/21-22:40:10,ISDN,EVENT_DISCONNECT:16,-,-
CDR,19,SIP:197.141.21.5,ISDN:1:1,021203407 <sip:02642102@195.191.28.110>, <sip:02642102@197.141.21.5>,0212038407,02642102,23/07/21-22:44:55,23/07/21-22:45:06,23/07/21-22:44:58,23/07/21-22:45:06,ISDN,EVENT_DISCONNECT:16,-,-
CDR,28,ISDN:1:1,SIP,100,0887639025,100 <sip:02642102@sip.iptel.co>,<sip:02642102@sip.iptel.co>,23/07/23-13:42:19,23/07/23-13:42:37,23/07/23-13:42:34,SIP,NUA_I_BYE:200,-,-
CDR,32,ISDN:1:1,SIP,100,013231111,100 <sip:013231111@sip.iptel.co>,<sip:013231111@sip.iptel.co>,23/07/23-14:12:19,23/07/23-14:12:33,-,-,ISDN,EVENT_DISCONNECT:16,-,-
""".strip()


@pytest.fixture(autouse=True)
def mock_port(mock_serial_port):
    return mock_serial_port


@pytest.fixture
def mock_plugin(mocker, mock_env):
    mock_env(
        plugin_beronet_ip="192.168.130.20",
        plugin_beronet_user="admin",
        plugin_beronet_password="admin",
    )
    plugin = call_plugin(beronet.BeroNet)
    mocked_stopped = mocker.patch.object(stopped, "is_set")
    mocked_stopped.side_effect = [False, True]
    yield plugin


##################################################################


def test_parser_all_good_lines(requests_mock, mock_plugin: beronet.BeroNet, disable_sleep):
    """Test that all good lines get parsed without errors."""
    mocked_request = requests_mock.get(mock_plugin.api_url, status_code=200, content=good_lines)
    successful = mock_plugin.run()

    assert successful
    assert mocked_request.called
    assert mock_plugin._queue.qsize() == len(good_lines.splitlines())


@pytest.mark.parametrize("raw_line", [
    b"CDR,19,SIP:197.141.21.5,ISDN:1:1,0212038407 <sip:02642102@195.191.28.110>, <sip:02642102@197.141.21.5>,0212038407,02642102,23/07/21-22:44:55,23/07/21-22:45:06,23/07/21-22:44:58,23/07/21-22:45:06,ISDN,EVENT_DISCONNECT:16,-,-",
])
def test_received_cdr(requests_mock, mock_plugin: beronet.BeroNet, disable_sleep, raw_line):
    requests_mock.get(mock_plugin.api_url, status_code=200, content=raw_line)

    assert mock_plugin.run()
    assert mock_plugin._queue.qsize() == len(raw_line.splitlines())

    record: CallDataRecord = mock_plugin._queue.get()
    assert record.call_type == CallDataRecord.RECEIVED
    assert record.number == "0212038407"
    assert record.date  # Assert that we have a date
    assert record.ring  # Assert that we have a ring time
    assert record.duration  # Assert that we have a duration


@pytest.mark.parametrize("raw_line", [
    b"CDR,18,ISDN:1:1,SIP,100,013231111,100 <sip:02642102@sip.iptel.co>,<sip:013231111@sip.iptel.co>,23/07/21-22:39:38,23/07/21-22:40:10,23/07/21-22:39:53,23/07/21-22:40:10,ISDN,EVENT_DISCONNECT:16,-,-",
])
def test_outgoing_cdr(requests_mock, mock_plugin: beronet.BeroNet, disable_sleep, raw_line):
    requests_mock.get(mock_plugin.api_url, status_code=200, content=raw_line)

    assert mock_plugin.run()
    assert mock_plugin._queue.qsize() == len(raw_line.splitlines())

    record: CallDataRecord = mock_plugin._queue.get()
    assert record.call_type == CallDataRecord.OUTGOING
    assert record.number == "013231111"
    assert record.date  # Assert that we have a date
    assert record.ring  # Assert that we have a ring time
    assert record.duration  # Assert that we have a duration


def test_wrong_status_code_no_error(requests_mock, mock_plugin: beronet.BeroNet, disable_sleep):
    """Test that the wrong status error gets caught and not cause an error."""
    requests_mock.get(mock_plugin.api_url, status_code=400)
    assert mock_plugin.run()  # This should return True if error was caught
