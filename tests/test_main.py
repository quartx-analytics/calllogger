# Third Party
from pytest_mock import MockerFixture

# Local
from calllogger import __main__ as entrypoint
from calllogger import settings


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
