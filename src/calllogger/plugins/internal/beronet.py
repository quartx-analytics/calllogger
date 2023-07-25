__all__ = ["BeroNet"]

# Standard library
from typing import NoReturn
from datetime import datetime
import csv

# Third Party
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from sentry_sdk import push_scope, capture_exception

# Local
from calllogger.plugins import BasePlugin
from calllogger.record import CallDataRecord as Record


class BeroNet(BasePlugin):
    """
    Collect call records continuously.
    Adds support for BeroNet virtual ISDN and VoIP CAPI
    Collects CDR as a CSV via HTTP API
    """
    # Matches with the ID of the
    # Phone system entry on the server.
    id = 2

    # Configurable settings
    beronet_ip: str
    beronet_user: str
    beronet_password: str
    beronet_sleep: int = 5

    def __init__(self):
        super(BeroNet, self).__init__()
        self.session = requests.Session()

    def entrypoint(self) -> NoReturn:
        while self.is_running:
            with push_scope() as scope:
                self.logger.debug("Collecting calls from beronet...")

                try:
                    cdr = self.collect()
                    self.process_cdr(cdr)
                except Exception as err:
                    scope.set_context("BeroNet", {
                        "beronet_ip": self.beronet_ip,
                        "beronet_user": self.beronet_user,
                    })
                    capture_exception(err, scope=scope)

                self.timeout.sleep(self.beronet_sleep)

    def collect(self) -> list[list[str]]:
        """Collect CDR from the BeroNet web API."""
        query_params = {
            "apiCommand": "TelephonyGetCdr",
            "Action": "download"
        }
        auth = HTTPBasicAuth(
            self.beronet_user,
            self.beronet_password,
        )
        url = f"http://{self.beronet_ip}/app/api/api.php"
        response = self.session.get(url=url, params=query_params, auth=auth)
        response.raise_for_status()

        if response.status_code == 200:
            decoded = response.content.decode('utf-8')
            cdr = csv.reader(decoded.splitlines(), delimiter=',')
            return list(cdr)
        else:
            # Anything other than 200 will raise HTTPError
            err_msg = "Unexpected response from beronet"
            self.logger.warning(
                f"{err_msg}: {response.status_code}",
                extra={"status_code": response.status_code},
            )
            raise HTTPError(err_msg, response=response)

    def process_cdr(self, cdr: list[list[str]]) -> NoReturn:
        """Process the CDR and create the required record."""
        for call in cdr:
            if call:
                # Deside if call is Outgoing or Received
                direction = call[2]
                if direction.startswith("ISDN"):
                    self.outgoing(call)
                else:
                    self.received(call)

    # noinspection PyMethodMayBeStatic
    def parse_dates(self, call: list[str], record: Record, fmt="%y/%m/%d-%H:%M:%S") -> NoReturn:
        """Parse and convert the CDR dates and calculate the extra fields."""
        start_date = datetime.strptime(call[8], fmt)
        end_date = datetime.strptime(call[9], fmt)
        record.date = start_date

        # Only calls that are answered will have a date here
        if call[10] != '-':
            ans_date = datetime.strptime(call[10], fmt)
            record.duration = int((end_date - ans_date).total_seconds())
            record.ring = int((ans_date - start_date).total_seconds())
            record.answered = True
        else:
            record.ring = int((end_date - start_date).total_seconds())
            record.answered = False

    def outgoing(self, call: list[str]) -> NoReturn:
        """Create call record for an outgoing call."""
        record = Record(call_type=Record.OUTGOING)
        record.number = call[5]
        record.ext = int(call[4])
        self.parse_dates(call, record)
        self.push(record)

    def received(self, call: list[str]) -> NoReturn:
        """Create call record for a received call."""
        record = Record(call_type=Record.RECEIVED)
        record.number = call[6]
        self.parse_dates(call, record)
        self.push(record)
