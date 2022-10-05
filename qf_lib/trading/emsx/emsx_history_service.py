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

from datetime import datetime
from typing import Optional, List

import blpapi
import pytz

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg.helpers import get_response_events
from qf_lib.settings import Settings
from qf_lib.trading.emsx.helpers import initialize_session, authorize_emsx_user
from qf_lib.trading.emsx.names import HISTORY_SERVICE_DEMO, HISTORY_SERVICE, GET_FILLS_RESPONSE
from qf_lib.trading.emsx.utils.data_objects import EMSXTransaction


class EMSXHistoryService:
    """
    EMSX history service provides individual fill information via request/response service. The service name is
    //blp/emsx.history for production and //blp/emsx.history.uat for test environment.

    The history service supports PARTIAL_RESPONSE events. The PARTIAL_RESPONSE event messages will return messages
    that are a subset of the information. The EMSX history service goes back up to 30 days in history.
    """

    def __init__(self, settings: Settings):
        self.host = settings.emsx.host
        self.port = settings.emsx.port
        self.username = settings.emsx.username
        self.uuid = settings.emsx.uuid
        self.local_configuration = settings.emsx.local
        self._local_timezone = pytz.timezone(settings.emsx.local_tz)

        self.service = HISTORY_SERVICE_DEMO if settings.emsx.test else HISTORY_SERVICE

        self.session = initialize_session(self.host, self.port)
        self.identity = None

        self.connected = False
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def connect(self):
        if not self.session.start():
            raise ConnectionError("Failed to start session.")
        self.logger.info("Session started successfully.")

        if not self.local_configuration:
            self.identity = authorize_emsx_user(self.session, self.host, self.username)

        if not self.session.openService(self.service):
            raise ConnectionError(f"Failed to open service: {self.service}")
        self.logger.info("Service started successfully.")

        self.connected = True

    def disconnect(self):
        if self.connected and not self.session.stop():
            self.logger.error("Cannot stop the session")
        else:
            self.connected = False

    def get_fills(self, start_date: datetime, end_date: Optional[datetime] = None) -> \
            List[EMSXTransaction]:
        """ Assumes local timezone. Returns Transactions with time converted to local timezone, with tzinfo parameter
        removed. """
        if not self.connected:
            self.connect()

        end_date = end_date or datetime.now()

        # Localize the start and end dates
        start_date = self._local_timezone.localize(start_date)
        end_date = self._local_timezone.localize(end_date)

        service = self.session.getService(self.service)
        request = service.createRequest("GetFills")
        request.set("FromDateTime", start_date)
        request.set("ToDateTime", end_date)

        scope = request.getElement("Scope")
        scope.getElement("Uuids").appendValue(self.uuid)

        self.session.sendRequest(request, correlationId=blpapi.CorrelationId(), identity=self.identity)
        return self._receive_fills_response()

    def _receive_fills_response(self):
        for event in get_response_events(self.session):
            for msg in event:
                if msg.messageType() == blpapi.Name("ErrorResponse"):
                    error_code = msg.getElementAsString("ErrorCode")
                    error_message = msg.getElementAsString("ErrorMsg")
                    self.logger.error(f"Error {error_code}: {error_message}")
                    raise BloombergError(f"Error {error_code}: {error_message}")
                elif msg.messageType() == GET_FILLS_RESPONSE:
                    return [self._parse_transaction(fill) for fill in msg.getElement("Fills").values()]

    def _parse_transaction(self, fill: blpapi.Element):
        try:
            order_reference_id = self._parse_order_reference_id(fill)
            order_id = fill.getElementAsInteger("OrderId")
            fill_id = fill.getElementAsInteger("FillId")
            price = fill.getElementAsFloat("FillPrice")
            commission = fill.getElementAsFloat("UserFees")
            currency = fill.getElementAsString("Currency")

            ticker = self._parse_ticker(fill)

            date_time_of_fill = fill.getElementAsDatetime("DateTimeOfFill")
            # Convert into UTC in order to avoid problems in case if no time zone is returned
            if date_time_of_fill.tzinfo is None:
                date_time_of_fill = pytz.utc.localize(date_time_of_fill)
            local_time_of_fill = date_time_of_fill.astimezone(self._local_timezone).replace(tzinfo=None)

            quantity = fill.getElementAsInteger("FillShares")
            emsx_side = fill.getElementAsString("Side")
            side = self._map_emsx_side(emsx_side)

            return EMSXTransaction(
                order_ref_id=order_reference_id,
                emsx_seq=order_id,
                fill_id=fill_id,
                price=price,
                time_value=local_time_of_fill,
                quantity=quantity,
                side=side,
                commission=commission,
                bbg_ticker=ticker,
                currency=currency
            )
        except Exception as e:
            self.logger.error(e)

    @staticmethod
    def _parse_order_reference_id(fill: blpapi.Element) -> Optional[int]:
        try:
            order_reference_id = fill.getElementAsString("OrderReferenceId") \
                if fill.hasElement("OrderReferenceId", True) else None
            order_reference_id = int(order_reference_id)
        except Exception:
            order_reference_id = None

        return order_reference_id

    @staticmethod
    def _map_emsx_side(emsx_side: str):
        emsx_side_mapping = {
            "B": "BUY",
            "S": "SELL"
        }

        try:
            return emsx_side_mapping[emsx_side]
        except KeyError:
            raise AttributeError(f"Unknown side detected: '{emsx_side}'") from None

    @staticmethod
    def _parse_ticker(fill: blpapi.Element) -> str:
        ticker = fill.getElementAsString("Ticker")
        exchange = fill.getElementAsString("Exchange")
        yellow_key = fill.getElementAsString("YellowKey")

        return f"{ticker} {exchange} {yellow_key}"
