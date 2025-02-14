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
from typing import Optional, Dict
from unittest import TestCase, skipIf
from unittest.mock import Mock

from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataarrays_equal
from qf_lib.tests.unit_tests.data_providers.bloomberg.config import REF_DATA_SERVICE_URI

try:
    import blpapi
    from blpapi.test import createEvent, appendMessage, MessageProperties, deserializeService
    from qf_lib.common.tickers.tickers import BloombergTicker
    from qf_lib.data_providers.bloomberg.bloomberg_names import SECURITIES, FIELDS, START_DATE, END_DATE, \
        PERIODICITY_SELECTION, PERIODICITY_ADJUSTMENT
    from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider

    is_bloomberg_installed = True
except ImportError:
    is_bloomberg_installed = False

from qf_lib.common.enums.frequency import Frequency


class Element:
    def __init__(self, name, value: Optional = None):
        self.name = name
        self.value = value

    def setValue(self, value):
        self.value = value

    def appendValue(self, value):
        if self.value is None:
            self.value = [value]
        else:
            self.value.append(value)

    def getElementAsFloat(self):
        return float(self.value)

    def getElementAsDatetime(self):
        return self.value

    def getElementAsString(self):
        return str(self.value)

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash(self.name, self.value)


class Request:
    def __init__(self, elements: Optional[Dict] = None):
        self.elements = elements if elements is not None else {}

    def getElement(self, name):
        if name not in self.elements:
            new_element = Element(name)
            self.elements[name] = new_element

        return self.elements[name]

    def set(self, name, value):
        element = self.getElement(name)
        element.setValue(value)

    def __eq__(self, other):
        return self.elements == other.elements


@skipIf(not is_bloomberg_installed, "No Bloomberg API installed. Tests are being skipped.")
class TestHistoricalDataProvider(TestCase):
    def setUp(self):
        # Mock the Reference Data Service
        self.ref_data_service = deserializeService(REF_DATA_SERVICE_URI)
        self.request_name = blpapi.Name("HistoricalDataRequest")

    def test_get_daily_frequency__test_request_payload(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        session.nextEvent.return_value = createEvent(5)

        data_provider = HistoricalDataProvider(session)
        data_provider.get([BloombergTicker("AAPL US Equity")], ["PX_LAST"], datetime(2025, 2, 6), datetime(2025, 2, 6),
                          Frequency.DAILY)

        expected_request = Request({
            SECURITIES: Element(SECURITIES, ["AAPL US Equity"]),
            FIELDS: Element(FIELDS, ["PX_LAST"]),
            START_DATE: Element(START_DATE, "20250206"),
            END_DATE: Element(END_DATE, "20250206"),
            PERIODICITY_SELECTION: Element(PERIODICITY_SELECTION, "DAILY"),
            PERIODICITY_ADJUSTMENT: Element(PERIODICITY_ADJUSTMENT, "ACTUAL")
        })
        session.sendRequest.assert_called_once_with(expected_request)

    def test_get_daily_frequency__single_ticker_multiple_dates_single_field(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData":
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": [
                        {"date": "2025-02-06", "PX_LAST": 138.53},
                        {"date": "2025-02-07", "PX_LAST": 138.72}
                    ],
                }
        }
        formatter.formatMessageDict(content)

        session.nextEvent.return_value = event

        data_provider = HistoricalDataProvider(session)
        result = data_provider.get([BloombergTicker("AAPL US Equity")], ["PX_LAST"], datetime(2025, 2, 6),
                                   datetime(2025, 2, 7), Frequency.DAILY)
        expected = QFDataArray.create(data=[[[138.53]], [[138.72]]], dates=[datetime(2025, 2, 6), datetime(2025, 2, 7)],
                                      tickers=[BloombergTicker("AAPL US Equity")], fields=["PX_LAST"])
        assert_dataarrays_equal(result, expected)

    def test_get_daily_frequency__single_ticker_single_date_multiple_fields(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData":
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": [
                        {"date": "2025-02-06", "PX_LAST": 138.53, "PX_VOLUME": 1000000},
                    ],
                }
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = HistoricalDataProvider(session)
        result = data_provider.get([BloombergTicker("AAPL US Equity")], ["PX_LAST", "PX_VOLUME"], datetime(2025, 2, 6),
                                   datetime(2025, 2, 6), Frequency.DAILY)
        expected = QFDataArray.create(data=[[[138.53, 1000000]]], dates=[datetime(2025, 2, 6)],
                                      tickers=[BloombergTicker("AAPL US Equity")], fields=["PX_LAST", "PX_VOLUME"])
        assert_dataarrays_equal(result, expected)
