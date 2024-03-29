# Standard lib
from datetime import datetime
from typing import Union
import json as _json
import logging
import sys

# Third party
import requests
from requests import codes
from sentry_sdk import push_scope, capture_exception, Scope

# Local
from calllogger.utils import Timeout
from calllogger import stopped, settings, auth, telemetry, __version__

logger = logging.getLogger("calllogger.api")
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
        self.timeout = Timeout(settings, stopped)
        self.suppress_errors = suppress_errors
        self.session = requests.Session()
        self.stopped = stopped

        # We register the logger here
        # so we can replace it elsewhere
        self.logger = logger

        # Add custom calllogger useragent
        self.session.headers["User-Agent"] = f"quartx-calllogger/{__version__}"

    def make_request(self, *args, **kwargs) -> requests.Response:
        """Contruct a request object and send the request."""
        custom_json = kwargs.pop("custom_json", None)
        request = requests.Request(*args, **kwargs)
        return self.send_request(request, custom_json)

    def send_request(self, request: requests.Request, custom_json=None, **kwargs) -> requests.Response:
        """Send request using a request object."""
        prepared_request = request.prepare()
        try:
            # Keep retrying to make the record if request fails
            while not self.stopped.is_set():
                with push_scope() as scope:
                    resp = self._send_request(scope, prepared_request, custom_json, kwargs)
                    if resp is True:
                        self.timeout.sleep()
                        self.logger.info("Retrying request", extra={"url": prepared_request.url})
                        continue
                    else:
                        return resp
        finally:
            self.timeout.reset()

    def _send_request(self, scope, request: requests.PreparedRequest, custom_json, kwargs) -> RetryResponse:
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
            kwargs.setdefault("timeout", 10.0)
            response = self.session.send(request, **kwargs)
            telemetry.track_http_resp_time(response)
            response.raise_for_status()
            return response

        except Exception as err:
            # Process the error and let sentry know
            retry = self.error_check(scope, err)
            request_scope(scope, request)
            scope.set_extra("retry", retry)
            capture_exception(err, scope=scope)
            err.sentry = True

            # Track request error metrics
            if isinstance(err, requests.HTTPError):
                telemetry.track_http_status_errors(err.response)
            else:
                telemetry.track_http_request_errors(request)

            # Return True if we need to retry, else re-raise the exception
            if retry is True:
                return True
            elif self.suppress_errors:
                return False
            else:
                # This will pervent too many errors
                # if we get stuck in a restart loop
                self.timeout.sleep()
                raise

    def error_check(self, scope, err: Exception) -> bool:
        """Check what kind of error we have and if we can safely retry the request."""

        # Extract url from err if possible, used for improving the logs
        url = getattr(getattr(err, "request", None), "url", "")

        # Server is unreachable, try again later
        if isinstance(err, requests.ConnectionError):
            self.logger.warning("Connection to server failed", extra={"url": url})
            return True

        # Request timed out, try again later
        elif isinstance(err, requests.Timeout):
            self.logger.warning("Connection to server timed out", extra={"url": url})
            return True

        # Check status code to deside what to do next
        elif isinstance(err, requests.HTTPError):
            self.logger.warning(
                "API request failed",
                extra={
                    "url": url,
                    "status_code": err.response.status_code,
                    "reason": err.response.reason,
                },
            )
            response_scope(scope, err.response)
            return self.status_check(err.response)
        else:
            self.logger.warning(str(err), extra={"url": url})
            return False

    def status_check(self, resp: requests.Response) -> bool:
        """
        Check the status of the response,
        Returning True if request needs to be retried.
        """

        # Quit if not authorized
        if resp.status_code in (codes.unauthorized, codes.payment_required, codes.forbidden):
            self.handle_unauthorized(resp)

        # Server is expereancing problems
        elif resp.status_code in (codes.not_found, codes.request_timeout) or resp.status_code >= codes.server_error:
            self.logger.warning("Server is experiencing problems.", extra={"url": resp.url})
            return True

        # Client sent Too Many Requests
        elif resp.status_code == codes.too_many_requests:
            # True will retry the request later after a small timeout
            retry_timeout = str(resp.headers.get("Retry-After", "")).strip()
            self.logger.warning("Rate limiting is enabled, Retrying request later", extra={
                "timeout": retry_timeout,
                "url": resp.url,
            })
            if retry_timeout.isdigit():  # pragma: no branch
                # Change the timeout value temporarily
                self.timeout.value = int(retry_timeout)
            return True
        else:
            self.logger.warning(
                "API request failed",
                extra={
                    "url": resp.url,
                    "status_code": resp.status_code,
                    "reason": resp.reason,
                },
            )

        # We don't know what other codes we might expect yet
        # So will default to False (No Retry)
        return False

    def handle_unauthorized(self, resp: requests.Response):
        """Called when a token is no longer authorized."""
        # This code is related to the cdr token
        # This will stay here as most use of it will be from CDR requests
        # When use is not related to the CDR (Influx), it will be overridden by that class then
        self.logger.info(
            "Quitting as the CDR token does not have the required permissions or has been revoked.",
            extra={
                "url": resp.url,
                "status_code": resp.status_code,
                "reason": resp.reason,
            },
        )
        auth.revoke_token()
        exit_code = 1
        self.stopped.set(exit_code)
        sys.exit(exit_code)
