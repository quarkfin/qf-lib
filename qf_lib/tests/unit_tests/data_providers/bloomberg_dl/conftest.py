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
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch

import jwt
import pytest
from requests import HTTPError

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.data_providers.bloomberg_dl.bloomberg_dl_data_provider import BloombergDLDataProvider
from qf_lib.data_providers.bloomberg_dl.utils.bloomberg_dl_parser import BloombergDLParser
from qf_lib.data_providers.bloomberg_dl.utils.bloomberg_dl_session import BloombergDLSession
from qf_lib.data_providers.bloomberg_dl.utils.sse_client import SSEEvent, SSEClient


@pytest.fixture
def data_provider():
    def _patched_init(self, _settings):
        self.reply_timeout = RelativeDelta(minutes=5)
        self.parser = Mock()
        self.save_to_disk = False
        self.downloads_path = None
        self._resource_lock = Mock()
        self._terminal_identity_user = None
        self._terminal_identity_sn = None
        self.session = Mock()
        self.catalog_id = "bbg0001"
        self.account_url = "https://api.bloomberg.com/eap/catalogs/bbg0001/"
        self.logger = Mock()

    with patch.object(BloombergDLDataProvider, "__init__", _patched_init):
        provider = BloombergDLDataProvider(Mock())
        provider.timer = SettableTimer(datetime(2025, 6, 10))
        yield provider


@pytest.fixture
def parser():
    return BloombergDLParser()


@pytest.fixture
def aapl_ticker():
    return BloombergTicker("AAPL US Equity")


@pytest.fixture
def msft_ticker():
    return BloombergTicker("MSFT US Equity")


@pytest.fixture
def spx_ticker():
    return BloombergTicker("SPX Index")


@pytest.fixture
def es_future_ticker():
    ft = BloombergFutureTicker("S&P 500 E-mini", "ES{} Index", 1, 1, 50)
    specific = BloombergTicker("ESZ1 Index", SecurityType.FUTURE, 50)
    ft.get_current_specific_ticker = Mock(return_value=specific)
    return ft


def get_mock_session(status_code=200, chunks=None):
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.raise_for_status = Mock()
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    mock_response.__iter__ = Mock(return_value=iter(chunks or []))
    mock_session.get.return_value = mock_response
    return mock_session


def get_mock_response(status_code=200, chunks=None, json_body=None, method="GET", url="http://test",
                      raise_error=False, **extra):
    resp = Mock()
    resp.status_code = status_code
    resp.headers = {}
    if raise_error:
        resp.raise_for_status.side_effect = HTTPError(f"{status_code} Error")
        resp.json.return_value = extra.get("json_body", {"error": "test"})
        resp.text = extra.get("text", "Error text")
    else:
        resp.raise_for_status = Mock()

    resp.request = Mock(method=method, url=url)
    resp.__iter__ = Mock(return_value=iter(chunks or []))
    if json_body is not None:
        resp.json.return_value = json_body
        resp.text = json.dumps(json_body)
    if status_code >= 400:
        http_error = HTTPError(response=resp)
        http_error.response = resp
        resp.raise_for_status.side_effect = http_error

    return resp


def get_mock_token(exp: float = None) -> str:
    exp = exp or (time.time() + 3600)
    return jwt.encode({"exp": exp}, "secret", algorithm="HS256")


@pytest.fixture
def session():
    fake_token = get_mock_token(exp=time.time() + 3600)
    with patch(f"{BloombergDLSession.__module__}.OAuth2Session") as mock_cls:
        mock_oauth = Mock()
        mock_oauth.fetch_token.return_value = {"access_token": fake_token}
        mock_oauth.headers = {}
        mock_cls.return_value = mock_oauth
        yield BloombergDLSession(client_id="test_id", client_secret="test_secret")


@pytest.fixture
def expired_session():
    fake_token = get_mock_token(exp=time.time() + 3600)
    with patch(f"{BloombergDLSession.__module__}.OAuth2Session") as mock_cls:
        mock_oauth = Mock()
        mock_oauth.fetch_token.return_value = {"access_token": fake_token}
        mock_oauth.headers = {}
        mock_cls.return_value = mock_oauth
        sess = BloombergDLSession(client_id="test_id", client_secret="test_secret")
        sess._token_expires_at = 0.0
        yield sess


RESPONSE_201_CREATED = {
    "@context": {"@vocab": "https://api.bloomberg.com/eap/ontology#",
                 "@base": "https://api.bloomberg.com/eap/catalogs/1234/requests/"},
    "@type": "Status", "title": "Created",
    "description": "The specified request was created", "statusCode": 201,
    "request": {"identifier": "eFGDJPCAdqm"},
}
RESPONSE_400_BAD_REQUEST = {
    "@context": {"@vocab": "https://api.bloomberg.com/eap/ontology#",
                 "@base": "https://api.bloomberg.com/eap/"},
    "@type": "Status", "statusCode": 400, "title": "Bad Request",
    "description": "The browser (or proxy) sent a request that this server could not understand.",
    "errors": [
        {"detail": "Invalid value provided.", "source": {"pointer": "/description", "location": "body"}},
        {"detail": "Invalid value provided.", "source": {"pointer": "/universe", "location": "body"}},
        {"detail": "Invalid value provided.", "source": {"pointer": "/formatting/dateFormat", "location": "body"}},
        {"detail": "Invalid value provided.", "source": {"pointer": "/terminalIdentity", "location": "body"}},
    ],
}
RESPONSE_401_UNAUTHORIZED = {
    "@context": {"@vocab": "https://api.bloomberg.com/eap/ontology#",
                 "@base": "https://api.bloomberg.com/eap/"},
    "@type": "Status", "statusCode": 401, "title": "Unauthorized",
    "description": ("The request has not been processed because it lacks valid authentication credentials "
                    "for the target resource. Refer to https://console.bloomberg.com to construct a valid JWT "
                    "to request this resource using either the Authorization header or query parameter."),
    "errors": [],
}

RESPONSE_500_INTERNAL_SERVER_ERROR = {
    "@context": {"@vocab": "https://api.bloomberg.com/eap/ontology#",
                 "@base": "https://api.bloomberg.com/eap/"},
    "@type": "Status", "statusCode": 500, "title": "Internal Server Error",
    "description": ("An error occurred while processing this request. Please follow best practices "
                    "to retry this request. If this issues persists, please enter a support ticket."),
    "errors": [],
}

CONTENT_DELIVERED_DATA = {"key": "goodRequestID-20231203T000444.bbg",
                          "headers": {
                              "Digest": "sha512=a4ad70085hg768852447b80195d74527847f559833ea117c",
                              "Content-Type": "text/vnd.blp.dl.std",
                              "Last-Modified": "Sun, 31 Dec 2026 12:12:12 GMT",
                              "Content-Length": 42
                          },
                          "metadata": {
                              "DL_REQUEST_ID": "goodRequestID",
                              "DL_SNAPSHOT_TZ": "EST",
                              "DL_REQUEST_NAME": "",
                              "DL_REQUEST_TYPE": "HistoryRequest",
                              "DL_SNAPSHOT_START_TIME": "2026-12-31T00:04:44"
                          }
                          }


def get_mock_content_delivered_event(request_id: str, request_type: str = "HistoryRequest") -> Mock:
    event = Mock()
    event.is_heartbeat.return_value = False
    data = CONTENT_DELIVERED_DATA
    data["metadata"]["DL_REQUEST_TYPE"] = request_type
    data["metadata"]["DL_REQUEST_ID"] = request_id
    event.data = json.dumps(data)
    return event


@pytest.fixture
def event():
    data_json = json.dumps(CONTENT_DELIVERED_DATA, separators=(",", ":"))
    return SSEEvent(f"id: contentID\nevent: ContentDelivered\ndata: {data_json}\n\n")


@pytest.fixture
def client():
    data_json = json.dumps(CONTENT_DELIVERED_DATA)
    raw_event = (f"id: contentID\nevent: ContentDelivered\n"
                 f"data: {data_json}\n\n").encode("utf-8")
    mock_session = get_mock_session(chunks=[raw_event])
    c = SSEClient("https://api.bloomberg.com/eap/notifications/content/responses", mock_session)
    yield c
    c.disconnect()
