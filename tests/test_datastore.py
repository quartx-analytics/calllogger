# Standard Lib
from pathlib import PosixPath
import base64

# Third Party
from pytest_mock import MockerFixture

# Local
from calllogger import datastore


def test_read(mocker: MockerFixture):
    """Test that datastore reads and decodes correctly."""
    encoded_data = base64.b64encode(b"testdata")
    mocked_open = mocker.patch.object(PosixPath, "open", mocker.mock_open(read_data=encoded_data))

    path = PosixPath("/data")
    value = datastore.read_datastore(path)

    mocked_open.assert_called_with("rb")
    assert mocked_open.return_value.read.called
    assert value == "testdata"


def test_write(mocker: MockerFixture):
    """Test that datastore writes encoded data."""
    encoded_data = base64.b64encode(b"testdata")
    mocked_open = mocker.patch.object(PosixPath, "open", mocker.mock_open())

    path = PosixPath("/data")
    datastore.write_datastore(path, "testdata")

    mocked_open.assert_called_with("wb")
    mocked_open.return_value.write.assert_called_with(encoded_data)
