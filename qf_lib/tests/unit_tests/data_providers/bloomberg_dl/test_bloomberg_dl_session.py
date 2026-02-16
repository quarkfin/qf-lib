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

import time
from unittest.mock import patch, Mock

import pytest
from requests.exceptions import HTTPError

from qf_lib.data_providers.bloomberg_dl.utils.bloomberg_dl_session import BloombergDLSession
from qf_lib.tests.unit_tests.data_providers.bloomberg_dl.conftest import get_mock_token, get_mock_response, session, \
    expired_session


def test_init_(session):
    assert session._session.headers["api-version"] == BloombergDLSession.API_VERSION
    assert session._token_expires_at > time.time()
    with patch(f"{BloombergDLSession.__module__}.OAuth2Session") as mock_cls:
        mock_oauth = Mock()
        mock_oauth.fetch_token.return_value = {}
        mock_oauth.headers = {}
        mock_cls.return_value = mock_oauth
        with pytest.raises(RuntimeError, match="Failed to obtain an access token"):
            BloombergDLSession(client_id="id", client_secret="secret")


def test_get__calls_session_get(session):
    session._session.get.return_value = get_mock_response(200)
    result = session.get("http://test/endpoint")
    session._session.get.assert_called_once_with("http://test/endpoint")
    assert result is session._session.get.return_value


def test_get__raises_on_http_error(session):
    session._session.get.return_value = get_mock_response(500, raise_error=True)
    with pytest.raises(HTTPError):
        session.get("http://test/endpoint")


def test_get__refreshes_token_when_expired(expired_session):
    new_token = get_mock_token(exp=time.time() + 7200)
    expired_session._session.fetch_token.return_value = {"access_token": new_token}
    expired_session._session.get.return_value = get_mock_response(200)
    expired_session.get("http://test/endpoint")
    assert expired_session._session.fetch_token.call_count >= 2


def test_post__calls_session_post(session):
    session._session.post.return_value = get_mock_response(201, method="POST")
    result = session.post("http://test/endpoint", json={"key": "val"})
    session._session.post.assert_called_once_with("http://test/endpoint", json={"key": "val"})
    assert result is session._session.post.return_value


def test_post__raises_on_http_error(session):
    session._session.post.return_value = get_mock_response(400, method="POST", raise_error=True)
    with pytest.raises(HTTPError):
        session.post("http://test/endpoint", json={})


def test_post__refreshes_token_when_expired(expired_session):
    new_token = get_mock_token(exp=time.time() + 7200)
    expired_session._session.fetch_token.return_value = {"access_token": new_token}
    expired_session._session.post.return_value = get_mock_response(201, method="POST")
    expired_session.post("http://test/endpoint")
    assert expired_session._session.fetch_token.call_count >= 2


def test_force_token_refresh__refreshes_the_token(session):
    new_token = get_mock_token(exp=time.time() + 7200)
    session._session.fetch_token.return_value = {"access_token": new_token}
    old_expires = session._token_expires_at
    session.force_token_refresh()
    assert session._token_expires_at >= old_expires
    assert session._session.fetch_token.call_count >= 2


def test_force_token_refresh__updates_access_token_on_session(session):
    new_token = get_mock_token(exp=time.time() + 7200)
    session._session.fetch_token.return_value = {"access_token": new_token}
    session.force_token_refresh()
    assert session._session.access_token == new_token
