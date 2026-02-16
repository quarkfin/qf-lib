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
from unittest.mock import Mock, MagicMock, patch

import pytest
from requests.exceptions import ChunkedEncodingError, HTTPError

from qf_lib.data_providers.bloomberg_dl.utils.sse_client import SSEEvent, SSEClient
from qf_lib.tests.unit_tests.data_providers.bloomberg_dl.conftest import get_mock_session, get_mock_response, event, \
    RESPONSE_401_UNAUTHORIZED, RESPONSE_500_INTERNAL_SERVER_ERROR, client


@pytest.mark.parametrize("raw,expected_heartbeat", [
    ("data:\n\n", True),
    ("", True),
    ('data: {"key": "value"}\n\n', False),
], ids=["empty_data", "empty_string", "with_data"])
def test_is_heartbeat(raw, expected_heartbeat):
    assert SSEEvent(raw).is_heartbeat() is expected_heartbeat


def test__init___parsing():
    assert SSEEvent('data: hello world\n\n').data == "hello world"
    assert SSEEvent("data: line1\ndata: line2\n\n").data == "line1\nline2"
    assert SSEEvent("event: ContentDelivered\ndata: {}\n\n").type == "ContentDelivered"
    assert SSEEvent('data: hello\n\n').type == "message"
    assert SSEEvent("id: 42\ndata: test\n\n").event_id == "42"
    assert SSEEvent("retry: 5000\ndata: test\n\n").retry == 5000
    assert SSEEvent(":this is a comment\ndata: hello\n\n").comments == "this is a comment"

    json_str = '{"key": "value", "number": 42}'
    assert SSEEvent(f"data: {json_str}\n\n").data == json_str

    # Delivered more complex content
    msg = (
        "event: ContentDelivered\n"
        "id: event001\n"
        'data: {"key": "output.json", "metadata": {"DL_REQUEST_ID": "req123"}}\n\n'
    )
    event = SSEEvent(msg)
    assert event.type == "ContentDelivered"
    assert event.event_id == "event001"
    assert '"DL_REQUEST_ID"' in event.data
    assert event.is_heartbeat() is False


def test__parse__event_properties(event):
    assert event.type == "ContentDelivered"
    assert event.event_id == "contentID"
    assert event.is_heartbeat() is False


def test__parse__data_payload(event):
    parsed = json.loads(event.data)
    assert parsed["key"] == "goodRequestID-20231203T000444.bbg"
    assert parsed["headers"]["Content-Type"] == "text/vnd.blp.dl.std"
    assert parsed["headers"]["Content-Length"] == 42
    assert parsed["metadata"]["DL_REQUEST_ID"] == "goodRequestID"
    assert parsed["metadata"]["DL_REQUEST_TYPE"] == "HistoryRequest"


def test__parse__multiline_data():
    part1 = '{"key": "goodRequestID-20231203T000444.bbg",'
    part2 = '"metadata": {"DL_REQUEST_ID": "goodRequestID"}}'
    event = SSEEvent(f"id: contentID\nevent: ContentDelivered\n"
                     f"data: {part1}\ndata: {part2}\n\n")
    assert event.type == "ContentDelivered"
    assert event.data == f"{part1}\n{part2}"


@pytest.fixture
def sse_client_with_data():
    chunks = [
        b'data: {"key": "out.json", "metadata": {"DL_REQUEST_ID": "r1"}}\n\n',
        b':\n\n',
    ]
    mock_session = get_mock_session(status_code=200, chunks=chunks)
    client = SSEClient("https://api.bloomberg.com/eap/notifications/content/responses", mock_session)
    yield client
    client.disconnect()


def test___init____connects_on_creation():
    mock_session = get_mock_session(chunks=[])
    client = SSEClient("https://example.com/sse", mock_session)
    mock_session.get.assert_called_once()
    client.disconnect()


def test___init____sets_headers():
    mock_session = get_mock_session(chunks=[])
    client = SSEClient("https://example.com/sse", mock_session)
    call_kwargs = mock_session.get.call_args[1]
    assert call_kwargs['headers']['Cache-Control'] == 'no-cache'
    assert call_kwargs['headers']['Accept'] == 'text/event-stream'
    client.disconnect()


def test___init____retries_on_401():
    mock_session = Mock()
    mock_session.get.side_effect = [
        MagicMock(status_code=401),
        MagicMock(status_code=200, raise_for_status=Mock(), **{'__iter__': Mock(return_value=iter([]))}),
    ]
    mock_session.force_token_refresh = Mock()
    client = SSEClient("https://example.com/sse", mock_session)
    mock_session.force_token_refresh.assert_called_once()
    assert mock_session.get.call_count == 2
    client.disconnect()


def test_disconnect__closes_event_source():
    mock_session = get_mock_session(chunks=[])
    client = SSEClient("https://example.com/sse", mock_session)
    client.disconnect()
    client.event_source.close.assert_called_once()


def test_disconnect__safe_when_event_source_is_none():
    mock_session = get_mock_session(chunks=[])
    client = SSEClient("https://example.com/sse", mock_session)
    client.event_source = None
    client.disconnect()


def test_disconnect__safe_when_close_raises():
    mock_session = get_mock_session(chunks=[])
    client = SSEClient("https://example.com/sse", mock_session)
    client.event_source.close.side_effect = RuntimeError("boom")
    client.disconnect()


def test_read_event__returns_data_event(sse_client_with_data):
    event = sse_client_with_data.read_event()
    assert isinstance(event, SSEEvent)
    assert event.is_heartbeat() is False
    assert '"DL_REQUEST_ID"' in event.data


def test_read_event__returns_heartbeat(sse_client_with_data):
    sse_client_with_data.read_event()
    assert sse_client_with_data.read_event().is_heartbeat() is True


def test_read_event__updates_retry_interval():
    mock_session = get_mock_session(chunks=[b"retry: 5000\ndata: hello\n\n"])
    client = SSEClient("https://example.com/sse", mock_session)
    client.read_event()
    assert client.retry_interval == 5.0
    client.disconnect()


def test_read_event__updates_last_id():
    mock_session = get_mock_session(chunks=[b"id: evt-42\ndata: hello\n\n"])
    client = SSEClient("https://example.com/sse", mock_session)
    client.read_event()
    assert client.last_id == "evt-42"
    client.disconnect()


def test_read_event__reconnects_on_stop_iteration():
    mock_session = Mock()
    r1 = MagicMock(status_code=200, raise_for_status=Mock())
    r1.__iter__ = Mock(return_value=iter([b"data: first\n\n"]))
    r2 = MagicMock(status_code=200, raise_for_status=Mock())
    r2.__iter__ = Mock(return_value=iter([b"data: second\n\n"]))
    mock_session.get.side_effect = [r1, r2]

    with patch("qf_lib.data_providers.bloomberg_dl.utils.sse_client.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        assert client.read_event().data == "first"
        assert client.read_event().data == "second"
    client.disconnect()


def test_read_event__raises_connection_error_after_max_reconnects():
    mock_session = Mock()
    resp = MagicMock(status_code=200, raise_for_status=Mock())
    resp.__iter__ = Mock(return_value=iter([]))
    mock_session.get.return_value = resp

    with patch("qf_lib.data_providers.bloomberg_dl.utils.sse_client.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        with pytest.raises(ConnectionError, match="Failed to read SSE event"):
            client.read_event()
    client.disconnect()


def test_read_event__reconnects_on_chunked_encoding_error():
    mock_session = Mock()
    r1 = MagicMock(status_code=200, raise_for_status=Mock())
    r1.__iter__ = lambda: (_ for _ in ()).throw(ChunkedEncodingError("reset"))
    r2 = MagicMock(status_code=200, raise_for_status=Mock())
    r2.__iter__ = Mock(return_value=iter([b"data: recovered\n\n"]))
    mock_session.get.side_effect = [r1, r2]

    with patch("qf_lib.data_providers.bloomberg_dl.utils.sse_client.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        assert client.read_event().data == "recovered"
    client.disconnect()


def test_read_event__default_retry_interval():
    mock_session = get_mock_session(chunks=[b"data: hi\n\n"])
    client = SSEClient("https://example.com/sse", mock_session)
    assert client.retry_interval == SSEClient.DEFAULT_RETRY_INTERVAL_MS / 1000.0
    client.disconnect()


def test_read_event__last_event_id_sent_on_reconnect():
    mock_session = Mock()
    r1 = MagicMock(status_code=200, raise_for_status=Mock())
    r1.__iter__ = Mock(return_value=iter([b"id: abc123\ndata: first\n\n"]))
    r2 = MagicMock(status_code=200, raise_for_status=Mock())
    r2.__iter__ = Mock(return_value=iter([b"data: second\n\n"]))
    mock_session.get.side_effect = [r1, r2]

    with patch("qf_lib.data_providers.bloomberg_dl.utils.sse_client.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        client.read_event()
        client.read_event()  # triggers reconnect
    reconnect_kwargs = mock_session.get.call_args_list[-1][1]
    assert reconnect_kwargs['headers'].get('Last-Event-ID') == 'abc123'
    client.disconnect()


def test_read_event__heartbeat_comment_only():
    mock_session = get_mock_session(chunks=[b":keep-alive\n\n"])
    client = SSEClient("https://example.com/sse", mock_session)
    event = client.read_event()
    assert event.is_heartbeat() is True and event.data == ""
    client.disconnect()


def test_read_event__heartbeat_does_not_update_last_id():
    mock_session = get_mock_session(chunks=[
        b"id: original-id\ndata: payload\n\n", b":\n\n"])
    client = SSEClient("https://example.com/sse", mock_session)
    client.read_event()
    assert client.last_id == "original-id"
    client.read_event()
    assert client.last_id == "original-id"
    client.disconnect()


def test_read_event__heartbeat_between_data_events():
    mock_session = get_mock_session(chunks=[
        b'data: first\n\n', b':\n\n', b'data: second\n\n'])
    client = SSEClient("https://example.com/sse", mock_session)
    assert client.read_event().data == "first"
    assert client.read_event().is_heartbeat() is True
    assert client.read_event().data == "second"
    client.disconnect()


def test_read_event__event_properties(client):
    event = client.read_event()
    assert event.type == "ContentDelivered"
    assert event.event_id == "contentID"
    assert event.is_heartbeat() is False

    # Make sure last id is updated
    assert client.last_id == "contentID"

    parsed = json.loads(event.data)
    assert parsed["key"] == "goodRequestID-20231203T000444.bbg"


def test_read_event__payload_details(client):
    parsed = json.loads(client.read_event().data)
    assert parsed["headers"]["Content-Type"] == "text/vnd.blp.dl.std"
    assert parsed["headers"]["Content-Length"] == 42
    assert parsed["metadata"]["DL_REQUEST_ID"] == "goodRequestID"
    assert parsed["metadata"]["DL_REQUEST_TYPE"] == "HistoryRequest"


def test__connect__401_triggers_token_refresh_then_succeeds():
    mock_session = Mock()
    mock_session.get.side_effect = [
        get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
        get_mock_response(status_code=200, chunks=[]),
    ]
    mock_session.force_token_refresh = Mock()
    client = SSEClient("https://example.com/sse", mock_session)
    mock_session.force_token_refresh.assert_called_once()
    assert mock_session.get.call_count == 2
    assert client.event_source.status_code == 200
    client.disconnect()


def test__connect__401_persists_after_refresh_raises():
    mock_session = Mock()
    mock_session.get.side_effect = [
        get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
        get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
    ]
    mock_session.force_token_refresh = Mock()
    with pytest.raises(HTTPError):
        SSEClient("https://example.com/sse", mock_session)
    assert mock_session.get.call_count == 2


def test_read_event__reconnect_after_401_refreshes_token():
    mock_session = Mock()
    mock_session.force_token_refresh = Mock()
    mock_session.get.side_effect = [
        get_mock_response(status_code=200, chunks=[b"data: first\n\n"]),
        get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
        get_mock_response(status_code=200, chunks=[b"data: second\n\n"]),
    ]
    with patch(f"{SSEClient.__module__}.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        assert client.read_event().data == "first"
        assert client.read_event().data == "second"
    mock_session.force_token_refresh.assert_called()
    client.disconnect()


def test_read_event__persistent_401_raises_connection_error():
    mock_session = Mock()
    mock_session.force_token_refresh = Mock()
    responses = [get_mock_response(status_code=200, chunks=[])]
    for _ in range(SSEClient.MAX_RECONNECT_ATTEMPTS):
        responses.extend([
            get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
            get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
        ])
    mock_session.get.side_effect = responses
    with patch(f"{SSEClient.__module__}.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        with pytest.raises(ConnectionError, match="Failed to read SSE event"):
            client.read_event()


def test_read_event__persistent_500_raises_connection_error():
    mock_session = Mock()
    responses = [get_mock_response(status_code=200, chunks=[])]
    for _ in range(SSEClient.MAX_RECONNECT_ATTEMPTS):
        responses.append(get_mock_response(status_code=500, json_body=RESPONSE_500_INTERNAL_SERVER_ERROR))
    mock_session.get.side_effect = responses
    with patch(f"{SSEClient.__module__}.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        with pytest.raises(ConnectionError, match="Failed to read SSE event"):
            client.read_event()


def test_read_event__500_then_401_then_success():
    mock_session = Mock()
    mock_session.force_token_refresh = Mock()
    mock_session.get.side_effect = [
        get_mock_response(status_code=200, chunks=[b"data: start\n\n"]),
        get_mock_response(status_code=500, json_body=RESPONSE_500_INTERNAL_SERVER_ERROR),
        get_mock_response(status_code=401, json_body=RESPONSE_401_UNAUTHORIZED),
        get_mock_response(status_code=200, chunks=[b"data: end\n\n"]),
    ]
    with patch(f"{SSEClient.__module__}.time.sleep"):
        client = SSEClient("https://example.com/sse", mock_session)
        assert client.read_event().data == "start"
        assert client.read_event().data == "end"
    mock_session.force_token_refresh.assert_called()
    client.disconnect()
