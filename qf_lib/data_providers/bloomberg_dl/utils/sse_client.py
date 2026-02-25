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

import re
import time

from requests.exceptions import ChunkedEncodingError

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class SSEEvent:
    """
    An event stream providing W3C Server-Sent Event (SSE) push-notifications of Bloomberg Data License Platform
    activity: https://html.spec.whatwg.org/multipage/
    """

    SSE_LINE_PATTERN = re.compile(r'(?P<name>[^:]*):?( ?(?P<value>.*))?')

    def __init__(self, event_string: str):
        self.data = None
        self.comments = None
        self.type = 'message'
        self.event_id = None
        self.retry = None
        self._parse(event_string)

    def _parse(self, event_string: str):
        """Parse a possibly-multiline string representing an SSE message and set corresponding attributes."""
        data_elements = []
        comment_elements = []

        for line in event_string.splitlines():
            if line.startswith(':'):
                comment_elements.append(line[1:])
                continue

            match = self.SSE_LINE_PATTERN.match(line)
            if match is None:
                continue

            name = match.group('name')
            value = match.group('value')
            if name == 'data':
                data_elements.append(value)
            elif name == 'event':
                self.type = value
            elif name == 'id':
                self.event_id = value
            elif name == 'retry':
                self.retry = int(value)

        self.data = '\n'.join(data_elements)
        self.comments = '\n'.join(comment_elements)

    def is_heartbeat(self) -> bool:
        """
        The notification API will periodically send out empty notifications that do not have any content to keep the
        connection alive. These heartbeat notifications can be ignored.
        """
        return self.data is None or self.data == ''


class SSEClient:
    """
    SSE client for receiving notifications from the Bloomberg DL REST API.

    Opens a persistent HTTP connection to the /eap/notifications/content/responses endpoint and yields parsed
    SSEEvent objects. Automatically reconnects on transient connection failures (up to MAX_RECONNECT_ATTEMPTS).

    Parameters
    ----------
    url: str
        full URL of the SSE endpoint (e.g. https://api.bloomberg.com/eap/notifications/content/responses)
    session: BloombergDLSession
        authenticated session used to establish the streaming connection
    """

    MAX_RECONNECT_ATTEMPTS = 3
    DEFAULT_RETRY_INTERVAL_MS = 3000

    def __init__(self, url: str, session):
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.url = url
        self.session = session
        self.event_source = None
        self.headers = {'Cache-Control': 'no-cache', 'Accept': 'text/event-stream'}
        self.last_id = None
        self.event_iterator = None
        self.retry_interval = self.DEFAULT_RETRY_INTERVAL_MS / 1000.0
        self._connect()

    def _connect(self):
        """Open a streaming connection to the SSE endpoint. If the server returns 401 (token expired), forces a
        token refresh on the session and retries once before raising."""
        if self.last_id:
            self.headers['Last-Event-ID'] = self.last_id
        self.logger.debug(f'Opening SSE connection to {self.url}')
        self.event_source = self.session.get(self.url, stream=True, headers=self.headers, raise_on_error=False)

        if self.event_source.status_code == 401:
            self.logger.warning('SSE connection returned 401 - forcing token refresh and retrying')
            self.session.force_token_refresh()
            self.event_source = self.session.get(self.url, stream=True, headers=self.headers, raise_on_error=False)

        self.event_source.raise_for_status()
        self.logger.info('SSE connection established')
        self.event_iterator = self._iter_events()

    def disconnect(self):
        """Close the SSE connection."""
        self.logger.info(f'Closing SSE connection to {self.url}')
        try:
            if self.event_source:
                self.event_source.close()
        except Exception:
            pass

    def _iter_events(self):
        """Iterate over the raw SSE stream and yield complete event strings (terminated by a blank line)."""
        data = ''
        for chunk in self.event_source:
            for line in chunk.splitlines(True):
                data += line.decode('utf-8')
                if data.endswith(('\r\r', '\n\n', '\r\n\r\n')):
                    yield data
                    data = ''
        if data:
            yield data

    def read_event(self) -> SSEEvent:
        """
        Read the next event from the SSE stream. Automatically reconnects on transient connection failures
        (up to MAX_RECONNECT_ATTEMPTS times). A 401 during reconnection triggers a forced token refresh.
        """
        last_exc = None
        for attempt in range(self.MAX_RECONNECT_ATTEMPTS):
            try:
                event_string = next(self.event_iterator)
                if not event_string:
                    raise EOFError("Empty event string received from SSE stream")

                event = SSEEvent(event_string)
                self.retry_interval = (event.retry or self.DEFAULT_RETRY_INTERVAL_MS) / 1000.0
                self.last_id = event.event_id or self.last_id
                return event
            except Exception as exc:
                last_exc = exc
                is_stream_drop = isinstance(exc, (ChunkedEncodingError, StopIteration, EOFError))
                if is_stream_drop:
                    self.logger.info(f"SSE connection dropped ({exc}), reconnect attempt "
                                     f"{attempt + 1}/{self.MAX_RECONNECT_ATTEMPTS}")
                else:
                    self.logger.warning(f"Error reading SSE event ({exc}), reconnect attempt "
                                        f"{attempt + 1}/{self.MAX_RECONNECT_ATTEMPTS}")
                try:
                    self._bounce_connection()
                except Exception as reconnect_exc:
                    last_exc = reconnect_exc
                    self.logger.warning(f"Reconnection failed ({reconnect_exc}), will retry if attempts remain")

        raise ConnectionError(
            f"Failed to read SSE event after {self.MAX_RECONNECT_ATTEMPTS} reconnect attempts"
        ) from last_exc

    def _bounce_connection(self):
        """Disconnect and reconnect after sleeping for the current retry interval."""
        self.disconnect()
        self.logger.debug(f'Sleeping {self.retry_interval}s before reconnecting')
        time.sleep(self.retry_interval)
        self._connect()
