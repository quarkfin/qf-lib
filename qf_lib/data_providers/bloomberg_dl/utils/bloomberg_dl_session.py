#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import threading
import time

import jwt
from oauthlib.oauth2 import BackendApplicationClient
from requests.exceptions import HTTPError
from requests_oauthlib import OAuth2Session

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class BloombergDLSession:
    """
    Thread-safe OAuth2 session wrapper for the Bloomberg DL REST API.

    Manages the full OAuth2 token lifecycle (acquisition and automatic refresh) and exposes HTTP methods
    (GET, POST, HEAD) that transparently ensure a valid token is present before every call.

    Parameters
    ----------
    client_id: str
        OAuth2 client identifier
    client_secret: str
        OAuth2 client secret corresponding to the client_id
    """

    OAUTH2_ENDPOINT = "https://bsso.blpprofessional.com/ext/api/as/token.oauth2"
    HOST = "https://api.bloomberg.com"
    API_VERSION = "2"

    # Refresh the token if less than 2 minutes remain before expiry. A bigger buffer is needed because
    # long-lived SSE connections embed the token at open-time - if the token expires while the stream is open the
    # server will drop the connection with `401 Client Error: Unauthorized for url`
    _TOKEN_REFRESH_THRESHOLD_SECONDS = 120

    def __init__(self, client_id: str, client_secret: str):
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self._client_id = client_id
        self._client_secret = client_secret
        self._token_expires_at: float = 0.0
        self._token_lock = threading.Lock()

        client = BackendApplicationClient(client_id=self._client_id)
        self._session = OAuth2Session(client=client)
        self._session.headers["api-version"] = self.API_VERSION

        self._request_token()

    def _request_token(self):
        """Fetch a fresh OAuth2 access token from the Bloomberg SSO endpoint."""
        token = self._session.fetch_token(token_url=self.OAUTH2_ENDPOINT, client_secret=self._client_secret)
        access_token = token.get("access_token")
        if not access_token:
            raise RuntimeError("Failed to obtain an access token from the Bloomberg DL REST API")

        self._session.access_token = access_token
        decoded = jwt.decode(jwt=access_token, options={"verify_signature": False})
        self._token_expires_at = float(decoded["exp"])
        self.logger.debug(f"OAuth2 token acquired, expires at epoch {self._token_expires_at}")

    def force_token_refresh(self):
        """Unconditionally refresh the token. Called by SSEClient when a 401 is received on (re)connection,
        indicating the token has expired server-side even though _ensure_valid_token thought it was still valid."""
        with self._token_lock:
            self.logger.info("Forced token refresh requested")
            self._request_token()

    def _ensure_valid_token(self):
        """Refresh the token if it is about to expire. Uses double-checked locking so that concurrent threads
        do not all attempt to refresh the token at the same time."""
        if time.time() >= self._token_expires_at - self._TOKEN_REFRESH_THRESHOLD_SECONDS:
            with self._token_lock:
                if time.time() >= self._token_expires_at - self._TOKEN_REFRESH_THRESHOLD_SECONDS:
                    self.logger.info("Token expired or about to expire - refreshing")
                    self._request_token()

    def get(self, url: str, raise_on_error: bool = True, **kwargs):
        """Thread-safe HTTP GET with automatic token refresh. When raise_on_error=False the response is returned
        even on non-2xx status codes (useful for 'check if resource exists' patterns)."""
        self._ensure_valid_token()
        response = self._session.get(url, **kwargs)
        self._log_response(response)
        if raise_on_error:
            self._raise_on_error(response)
        return response

    def post(self, url: str, raise_on_error: bool = True, **kwargs):
        """Thread-safe HTTP POST with automatic token refresh."""
        self._ensure_valid_token()
        response = self._session.post(url, **kwargs)
        self._log_response(response)
        if raise_on_error:
            self._raise_on_error(response)
        return response

    def head(self, url: str, raise_on_error: bool = True, **kwargs):
        """Thread-safe HTTP HEAD with automatic token refresh."""
        self._ensure_valid_token()
        response = self._session.head(url, **kwargs)
        self._log_response(response)
        if raise_on_error:
            self._raise_on_error(response)
        return response

    def _log_response(self, response):
        """Log basic request / response information at DEBUG level."""
        self.logger.debug(f"HTTP {response.request.method} {response.request.url} -> {response.status_code} "
                          f"(x-request-id: {response.headers.get('x-request-id')})")

    def _raise_on_error(self, response):
        """Raise on HTTP errors and log details."""
        try:
            response.raise_for_status()
        except HTTPError:
            try:
                details = response.json()
            except Exception:
                details = response.text
            self.logger.error(f"Unexpected response {response.status_code} from {response.request.url} - {details}")
            raise
