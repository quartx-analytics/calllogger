from quartx_call_logger import config
from unittest import mock


# def test_user_config():
#     read_data = "settings:\n  timeout: 20"
#     with mock.patch("os.path.exists", return_value=True):
#         with mock.patch("__main__.open", mock.mock_open(read_data="")) as open_mock:
#             def work():
#                 print("dfdfdf")
#
#             open_mock.side_effect = work
#             settings = config.compile_settings()
#             assert settings["timeout"] == 20
