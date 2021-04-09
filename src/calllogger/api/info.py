# Third party
import requests

# Local
from calllogger.conf import settings


def get_owner_info() -> dict[str, ]:
    return dict(
        id=settings.token,
        username="Test Tenant",
        email="test@quartx.ie",
    )
