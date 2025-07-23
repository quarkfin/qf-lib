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
from unittest import skipIf, TestCase
from unittest.mock import Mock

from numpy import nan

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal
from qf_lib.tests.unit_tests.data_providers.bloomberg.config import REF_DATA_SERVICE_URI
from qf_lib.tests.unit_tests.data_providers.bloomberg.mock_configs import Request

try:
    import blpapi
    from blpapi.test import createEvent, appendMessage, deserializeService
    from qf_lib.common.tickers.tickers import BloombergTicker
    from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider

    is_bloomberg_installed = True
except ImportError:
    is_bloomberg_installed = False


@skipIf(not is_bloomberg_installed, "No Bloomberg API installed. Tests are being skipped.")
class TestReferenceDataProvider(TestCase):
    def setUp(self):
        # Mock the Reference Data Service
        self.ref_data_service = deserializeService(REF_DATA_SERVICE_URI)
        self.request_name = blpapi.Name("ReferenceDataRequest")

    def test_get__single_ticker__single_field(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData": [
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {"PX_LAST": 138.53},
                }
            ]
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        result = data_provider.get([BloombergTicker("AAPL US Equity")], ["PX_LAST"])
        expected = QFDataFrame(data={"PX_LAST": [138.53]}, index=[BloombergTicker("AAPL US Equity")])
        assert_dataframes_equal(result, expected)

    def test_get_field_exception(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData": [
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {},
                    "fieldExceptions": [
                        {
                            "fieldId": "Bonjour!",
                            "errorInfo": {
                                "source": "src",
                                "code": 5,
                                "category": "NO_AUTH",
                                "message": "Field..",
                                "subcategory": "FIELD..",
                            },
                        }
                    ],
                },
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {"PX_LAST": 138.53},
                }
            ]
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        data_provider.logger = Mock()
        result = data_provider.get([BloombergTicker("AAPL US Equity")], ["Bonjour!", "PX_LAST"])
        expected = QFDataFrame(data={"Bonjour!": [None], "PX_LAST": [138.53]},
                               index=[BloombergTicker("AAPL US Equity")])
        assert_dataframes_equal(result, expected)
        data_provider.logger.warning.assert_called_once()

    def test_get__multiple_tickers_security_error(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData": [
                {
                    "security": "Hehe US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {},
                    "fieldExceptions": [],
                    "securityError": {
                        "source": "21932:rsfrdsvc1",
                        "code": 43,
                        "category": "BAD_SEC",
                        "message": "Unknown/Invalid Security  [nid:21932]",
                        "subcategory": "INVALID_SECURITY"
                    }
                },
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {"PX_LAST": 138.53},
                }
            ]
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        data_provider.logger = Mock()
        result = data_provider.get([BloombergTicker("AAPL US Equity"), BloombergTicker("Hehe US Equity")], ["PX_LAST"])
        expected = QFDataFrame(data={"PX_LAST": [138.53, nan]},
                               index=[BloombergTicker("AAPL US Equity"), BloombergTicker("Hehe US Equity")])
        assert_dataframes_equal(result, expected)
        data_provider.logger.error.assert_called_once()

    def test_get__single_ticker_security_error(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData": [
                {
                    "security": "Hehe US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {},
                    "fieldExceptions": [],
                    "securityError": {
                        "source": "something",
                        "code": 43,
                        "category": "BAD_SEC",
                        "subcategory": "INVALID_SECURITY"
                    }
                },
            ]
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        data_provider.logger = Mock()
        result = data_provider.get([BloombergTicker("Hehe US Equity")], ["PX_LAST"])
        expected = QFDataFrame(data={"PX_LAST": [nan]},
                               index=[BloombergTicker("Hehe US Equity")])
        assert_dataframes_equal(result, expected)
        data_provider.logger.error.assert_called_once()

    def test_get__multiple_tickers_multiple_fields(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData": [
                {
                    "security": "AAPL US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {"PX_LAST": 138.53},
                },
                {
                    "security": "IBM US Equity",
                    "sequenceNumber": 0,
                    "fieldData": {"PX_LAST": 158.53},
                }
            ]
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        result = data_provider.get([BloombergTicker("AAPL US Equity"), BloombergTicker("IBM US Equity")], ["PX_LAST"])
        expected = QFDataFrame(data={"PX_LAST": [138.53, 158.53]},
                               index=[BloombergTicker("AAPL US Equity"), BloombergTicker("IBM US Equity")])
        assert_dataframes_equal(result, expected)

    def test_response_error(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "responseError":
                {
                    "source": "something",
                    "code": 43,
                    "category": "LIMIT",
                    "message": "Access pending review",
                    "subcategory": "REVIEW"
                },
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        data_provider.logger = Mock()
        data_provider.get([BloombergTicker("AAPL US Equity")], ["PX_LAST"])
        data_provider.logger.error.assert_called_once()

    def test_get_tabular_data__non_tabular_field(self):
        session = Mock()
        session.getService.return_value.createRequest.return_value = Request()
        event = createEvent(blpapi.Event.RESPONSE)

        schema = self.ref_data_service.getOperation(
            self.request_name
        ).getResponseDefinitionAt(0)

        formatter = appendMessage(event, schema)
        content = {
            "securityData": [
                {
                    "security": "Test Index",
                    "sequenceNumber": 0,
                    "fieldData": {
                        "INDEX_MEMBERS_WEIGHTS": [
                            {"Index Member": "A US", "Weight": 0.01},
                            {"Index Member": "B US", "Weight": 0.02}
                        ],
                    },
                }
            ]
        }
        formatter.formatMessageDict(content)
        session.nextEvent.return_value = event

        data_provider = ReferenceDataProvider(session)
        result = data_provider.get([BloombergTicker("Test Index")], ["INDEX_MEMBERS_WEIGHTS"])
        expected = QFDataFrame(data={"INDEX_MEMBERS_WEIGHTS": [[{"Index Member": "A US", "Weight": 0.01},
                                                                {"Index Member": "B US", "Weight": 0.02}]]},
                               index=[BloombergTicker("Test Index")])
        self.assertEqual(result.shape, expected.shape)
        self.assertCountEqual(result.iloc[0, 0], expected.iloc[0, 0])
