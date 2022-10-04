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
from typing import List
from unittest import TestCase
from unittest.mock import Mock, patch

import blpapi

from qf_lib.tests.unit_tests.trading.emsx.config import EMSX_HISTORY_SERVICE
from qf_lib.trading.emsx.emsx_history_service import EMSXHistoryService
from qf_lib.trading.emsx.utils.data_objects import EMSXTransaction


class TestEMSXHistoryService(TestCase):

    @patch("brokers.emsx.helpers.blpapi")
    def setUp(self, _) -> None:
        self.service = blpapi.test.deserializeService(EMSX_HISTORY_SERVICE)
        self.request_name = blpapi.Name("GetFills")

        settings = Mock()
        settings.emsx.service = self.service
        settings.emsx.uuid = 1234
        settings.emsx.local_tz = "Europe/Zurich"

        self.emsx_history_service = EMSXHistoryService(settings)
        self.emsx_history_service.session = Mock()

    def test_get_fills__single_fill(self):
        """
        Test get_fills function in case if one response with one fill is delivered. The delivered fill
        is a BUY transaction.
        """
        messages = [{
            "Fills": [
                {
                    "OrderReferenceId": "12345",
                    "OrderId": 1,
                    "FillId": 3,
                    "FillPrice": 138.53,
                    "Currency": "USD",
                    "DateTimeOfFill": '2021-12-01T05:00:00.000-05:00',
                    "FillShares": 5,
                    "Side": "B",
                    "UserFees": 1.5,
                }
            ]
        }]
        self.mock_response_messages(messages)
        transactions = self.emsx_history_service.get_fills(datetime(2021, 12, 1), datetime(2021, 12, 2))
        self.assertEqual(len(transactions), 1)

        expected_transaction = EMSXTransaction(
            int_order_id=12345,
            ext_order_id=1,
            fill_id=3,
            price=138.53,
            time_value=datetime(2021, 12, 1, 11, 0),
            quantity=5,
            side="BUY",
            commission=1.5,
        )
        self.assertEqual(transactions[0], expected_transaction)

    def test_get_fills__multiple_fills(self):
        """ Test get fills in case of multiple fills. Check both types of sides: B and S. """
        messages = [{
            "Fills": [
                {
                    "OrderReferenceId": "12345",
                    "OrderId": 1,
                    "FillId": 3,
                    "FillPrice": 138.53,
                    "DateTimeOfFill": '2021-12-01T05:00:00.000-05:00',
                    "FillShares": 5,
                    "Side": "B",
                    "UserFees": 1.5,
                }, {
                    "OrderReferenceId": "12346",
                    "OrderId": 2,
                    "FillId": 3,
                    "FillPrice": 137.53,
                    "DateTimeOfFill": '2021-12-01T05:10:00.000-05:00',
                    "FillShares": 3,
                    "Side": "S",
                    "UserFees": 1.5,
                }
            ]
        }]
        self.mock_response_messages(messages)
        transactions = self.emsx_history_service.get_fills(datetime(2021, 12, 1), datetime(2021, 12, 2))
        self.assertEqual(len(transactions), 2)

        expected_transactions = [
            EMSXTransaction(
                int_order_id=12345,
                ext_order_id=1,
                fill_id=3,
                price=138.53,
                time_value=datetime(2021, 12, 1, 11, 0),
                quantity=5,
                side="BUY",
                commission=1.5
            ), EMSXTransaction(
                int_order_id=12346,
                ext_order_id=2,
                fill_id=3,
                price=137.53,
                time_value=datetime(2021, 12, 1, 11, 10),
                quantity=3,
                side="SELL",
                commission=1.5
            )]
        self.assertCountEqual(transactions, expected_transactions)

    def test_get_fills__invalid_fills(self):
        """ Test behaviour in case if a fill message does not have all necessary fields or if
        the side parameter is not valid. """
        invalid_messages = [{
            "Fills": [
                {
                    "OrderId": 1,
                    "FillId": 3,
                    "FillPrice": 138.53,
                    "FillShares": 5,
                    "Side": "B",
                    "UserFees": 1.5,
                }, {
                    "OrderReferenceId": "12346",
                    "OrderId": 2,
                    "FillId": 3,
                    "FillPrice": 137.53,
                    "DateTimeOfFill": '2021-12-01T05:10:00.000-05:00',
                    "FillShares": 3,
                    "Side": "X",
                    "UserFees": 1.5,
                }
            ]
        }]
        self.mock_response_messages(invalid_messages)
        transactions = self.emsx_history_service.get_fills(datetime(2021, 12, 2), datetime(2021, 12, 2))
        self.assertEqual(len(transactions), 0)

    def test_get_fills__different_timezones(self):
        messages = [{
            "Fills": [
                {
                    "OrderReferenceId": "12345",
                    "OrderId": 1,
                    "FillId": 3,
                    "FillPrice": 138.53,
                    "DateTimeOfFill": '2021-12-01T05:00:00.000-05:00',
                    "FillShares": 5,
                    "Side": "B",
                    "UserFees": 1.5,
                },
            ]
        }]
        self.mock_response_messages(messages)

        transactions = self.emsx_history_service.get_fills(datetime(2021, 12, 1), datetime(2021, 12, 2))
        self.assertEqual(transactions[0].time_value, datetime(2021, 12, 1, 11))

    def mock_response_messages(self, messages: List):
        event = blpapi.test.createEvent(blpapi.event.Event.RESPONSE)
        schema = self.service.getOperation(self.request_name).getResponseDefinitionAt(0)

        for message in messages:
            formatter = blpapi.test.appendMessage(event, schema)
            formatter.formatMessageDict(message)

        self.emsx_history_service.session.nextEvent.return_value = event
