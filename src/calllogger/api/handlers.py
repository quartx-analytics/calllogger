# Standard lib
from datetime import datetime
from typing import Union
import json as _json
import logging

# Third party
import requests
from requests import codes
from sentry_sdk import push_scope, capture_exception, Scope

# Local
from calllogger.utils import Timeout
from calllogger.conf import settings
from calllogger import running

logger = logging.getLogger(__name__)
RetryResponse = Union[bool, requests.Response]


def request_scope(scope: Scope, request: requests.PreparedRequest):
    """Take a sentry scope and request object to build sentry contexts."""
    scope.set_context("Request", dict(
        method=request.method,
        headers=request.headers,
        body=request.body,
        url=request.url,
    ))


def response_scope(scope: Scope, response: requests.Response):
    """Take a sentry scope and response object to build sentry contexts."""
    scope.set_context("Response", dict(
        body=decode_response(response),
        status_code=response.status_code,
        elapsed=response.elapsed,
        reason=response.reason,
    ))


def decode_response(response: requests.Response, limit=1000) -> Union[str, dict]:
    """
    Decode requests response body using json if
    possible else limit body to 1000 characters.
    """
    try:
        data = response.json()
    except _json.decoder.JSONDecodeError:
        logger.debug("Error response was not a valid json response")
        return response.text[:limit]
    else:
        return data[:limit] if isinstance(data, str) else data


class ComplexEncoder(_json.JSONEncoder):
    """Custom Json Encoder to serialize other types of python objects."""

    def default(self, obj):
        # Decode datetime objects to iso format
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Let the base class default method raise the TypeError
        return super().default(obj)


class QuartxAPIHandler:
    """Custom Requests handler for api errors."""

    def __init__(self, *args, suppress_errors=False, **kwargs):
        super(QuartxAPIHandler, self).__init__(*args, **kwargs)
        self.timeout = Timeout(settings, running.is_set)  # pragma: no branch
        self.suppress_errors = suppress_errors
        self.session = requests.Session()
        self.running = running

    def make_request(self, *args, **kwargs) -> requests.Response:
        """Contruct a request object and send the request."""
        custom_json = kwargs.pop("custom_json", None)
        request = requests.Request(*args, **kwargs)
        return self.send_request(request, custom_json)

    def send_request(self, request: requests.Request, custom_json: dict = None, **kwargs) -> requests.Response:
        """Send request using a request object."""
        prepared_request = request.prepare()
        try:
            # Keep retrying to make the record if request fails
            while self.running.is_set():
                with push_scope() as scope:
                    resp = self._send_request(scope, prepared_request, custom_json, kwargs)
                    if resp is True:
                        self.timeout.sleep()
                        continue
                    else:
                        return resp
        finally:
            self.timeout.reset()

    def _send_request(self, scope, request: requests.PreparedRequest, custom_json: dict, kwargs) -> RetryResponse:
        """
        Send request and process the response for errors.
        Returning True if request needs to be retried.
        """
        try:
            # Add request body
            if custom_json:
                data = _json.dumps(custom_json, cls=ComplexEncoder)
                request.headers["content-type"] = "application/json"
                request.prepare_body(data, None)

            # Send Request
            response = self.session.send(request, timeout=self.timeout.value, **kwargs)
            response.raise_for_status()
            return response

        except Exception as err:
            # Process the error and let sentry know
            retry = self.error_check(scope, err)
            request_scope(scope, request)
            scope.set_extra("retry", retry)
            capture_exception(err, scope=scope)
            err.sentry = True

            # Return True if we need to retry, else re-raise the exception
            if retry is True:
                return True
            elif self.suppress_errors:
                return False
            else:
                raise

    def error_check(self, scope, err: Exception) -> bool:
        """Check what kind of error we have and if we can safely retry the request."""

        # Server is unreachable, try again later
        if isinstance(err, (requests.ConnectionError, requests.Timeout)):
            logger.warning("Connection to server failed/timed out")
            return True

        # Check status code to deside what to do next
        elif isinstance(err, requests.HTTPError) and err.response is not None:
            logger.warning(
                "API request failed with status code: %s %s",
                err.response.status_code,
                err.response.reason
            )
            response_scope(scope, err.response)
            return self.status_check(err.response.status_code)
        else:
            logger.warning(str(err))
            return False

    def status_check(self, status_code) -> bool:
        """
        Check the status of the response,
        Returning True if request needs to be retried.
        """

        # Quit if not authorized
        if status_code in (codes.unauthorized, codes.payment_required, codes.forbidden):
            logger.error("Quitting as the token does not have the required permissions or has been revoked.")
            self.running.clear()
            return False

        # Server is expereancing problems, reattempting request later
        elif status_code in (codes.not_found, codes.request_timeout) or status_code >= codes.server_error:
            logger.warning("Server is experiencing problems.")
            return True
