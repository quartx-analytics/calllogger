# Standard Lib
from contextlib import redirect_stdout
import io

# Third Party
from pytest_mock import MockerFixture

# Local
from calllogger import __main__ as entrypoint
from calllogger import settings


def test_getid():
    # Mocked stdout
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        ret = entrypoint.getid()
        assert ret == 0

    output = stdout.getvalue()
    assert output.strip() == settings.identifier


def test_monitor(mocker: MockerFixture):
    mocked_loop = mocker.patch.object(entrypoint, "main_loop", return_value=0)
    ret = entrypoint.monitor()
    assert ret == 0
    mocked_loop.assert_called_with(settings.plugin)


def test_mockcalls(mocker: MockerFixture):
    mocked_loop = mocker.patch.object(entrypoint, "main_loop", return_value=0)
    ret = entrypoint.mockcalls()
    assert ret == 0
    mocked_loop.assert_called_with("MockCalls")
