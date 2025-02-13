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
from datetime import datetime, timedelta
from typing import Optional
from unittest import TestCase
from unittest.mock import patch, Mock

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider import BloombergBeapHapiDataProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_request_provider import \
    BloombergBeapHapiRequestsProvider


class TestBloombergBeapHapiDataProvider(TestCase):

    def setUp(self) -> None:
        def __init__(_self, _):
            field_to_type = {
                "PX_LAST": "float"
            }
            _self.fields_hapi_provider = Mock()
            _self.fields_hapi_provider.get_fields_history_url.return_value = (Mock(), field_to_type)
            _self.fields_hapi_provider.get_fields_url.return_value = (Mock(), Mock())
            _self.universe_hapi_provider = Mock()
            _self.request_hapi_provider = Mock()
            _self.parser = Mock()
            _self.connected = True
            _self.reply_timeout = timedelta(minutes=0)
            _self.logger = Mock()
            _self.sse_client = Mock()

        beap_hapi_patcher = patch.object(BloombergBeapHapiDataProvider, '__init__', __init__)
        beap_hapi_patcher.start()
        self.addCleanup(beap_hapi_patcher.stop)

        self.data_provider = BloombergBeapHapiDataProvider(Mock())
        self.data_provider.timer = SettableTimer(datetime(2025, 2, 10))

    def test_get_tickers_universe__invalid_date(self):
        with self.assertRaises(ValueError):
            self.data_provider.get_tickers_universe(BloombergTicker("Example Index"), datetime(1970, 1, 1))

    def test_get_tickers_universe__valid_ticker(self):
        self.data_provider.parser.get_current_values.return_value = QFDataFrame.from_records(
            [(BloombergTicker("SPX Index"), ["Member1", "Member2"]), ],
            columns=["Ticker", "INDEX_MEMBERS_WEIGHTS"]).set_index("Ticker")

        universe = self.data_provider.get_tickers_universe(BloombergTicker("SPX Index"))
        self.assertCountEqual(universe, [BloombergTicker("Member1 Equity"), BloombergTicker("Member2 Equity")])

    def test_get_tickers_universe__invalid_ticker(self):
        self.data_provider.parser.get_current_values.return_value = QFDataFrame.from_records(
            [(BloombergTicker("Invalid Index"), []), ], columns=["Ticker", "INDEX_MEMBERS_WEIGHTS"]).set_index("Ticker")

        universe = self.data_provider.get_tickers_universe(BloombergTicker("Invalid Index"))
        self.assertCountEqual(universe, [])

    """ Test get_history for SettableTimer """

    def test_get_history__incorrect_frequency(self):
        with self.assertRaises(NotImplementedError):
            self.data_provider.get_history(tickers=BloombergTicker("AAPL US Equity"), fields="PX_LAST",
                                           start_date=datetime(2025, 2, 7),
                                           end_date=datetime(2025, 2, 7), frequency=Frequency.SEMI_ANNUALLY,
                                           look_ahead_bias=True)

    def test_get_history__single_field_single_ticker_single_date_daily(self):
        ticker = BloombergTicker("AAPL US Equity")
        dates = [datetime(2025, 2, 7)]
        data = [[[100.0]]]
        self.data_provider.parser.get_history.return_value = QFDataArray.create(data=data, dates=dates,
                                                                                tickers=[ticker], fields=["PX_LAST"])
        result = self.data_provider.get_history(tickers=ticker, fields="PX_LAST", start_date=datetime(2025, 2, 7),
                                                end_date=datetime(2025, 2, 7), frequency=Frequency.DAILY,
                                                look_ahead_bias=True)
        expected_result = 100.0
        self.assertEqual(result, expected_result)

    def test_get_history__single_field_single_ticker_multiple_dates_daily(self):
        ticker = BloombergTicker("AAPL US Equity")
        dates = [datetime(2025, 2, 6), datetime(2025, 2, 7)]
        data = [[[100.0]], [[101.0]]]
        self.data_provider.parser.get_history.return_value = QFDataArray.create(data=data, dates=dates,
                                                                                tickers=[ticker], fields=["PX_LAST"])
        result = self.data_provider.get_history(tickers=ticker, fields="PX_LAST", start_date=datetime(2025, 2, 6),
                                                end_date=datetime(2025, 2, 7), frequency=Frequency.DAILY,
                                                look_ahead_bias=True)
        expected_result = QFSeries([100.0, 101.0], index=dates)
        self.assertTrue(result.equals(expected_result))

    def test_get_history__multiple_fields_multiple_tickers_multiple_dates_daily(self):
        tickers = [BloombergTicker("AAPL US Equity"), BloombergTicker("MSFT US Equity")]
        dates = [datetime(2025, 2, 6), datetime(2025, 2, 7)]
        data = [[[100.0, 101.0], [200.0, 201.0]], [[5000, 5200], [10000, 10200]]]
        data_array = QFDataArray.create(data=data, dates=dates, tickers=tickers, fields=["PX_LAST", "VOLUME"])
        self.data_provider.parser.get_history.return_value = data_array
        result = self.data_provider.get_history(tickers=tickers, fields=["PX_LAST", "VOLUME"],
                                                start_date=datetime(2025, 2, 6), end_date=datetime(2025, 2, 7),
                                                frequency=Frequency.DAILY, look_ahead_bias=True)
        self.assertTrue(result.equals(data_array))

    def test_supported_tickers(self):
        self.assertCountEqual({BloombergTicker, BloombergFutureTicker}, self.data_provider.supported_ticker_types())

    def test_supported_frequencies(self):
        self.assertCountEqual(
            {Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY, Frequency.QUARTERLY, Frequency.YEARLY},
            self.data_provider.supported_frequencies())

    """ Test the payload of created get_history requests """

    def __test_payload_creation(self, terminal_identity_user: Optional[str] = None,
                                terminal_identity_sn: Optional[str] = None):
        # Step 1: Prepare the parser get_history dummy output and mock the datetime.now
        self.data_provider.parser.get_history.return_value = QFDataArray.create(
            data=[[[200]]], dates=[datetime(2025, 2, 6)], tickers=[BloombergTicker("AAPL US Equity")],
            fields=["PX_LAST"])

        # Step 2: Set up the Request Provider
        session = Mock()
        # When the request is being created, initially no resources exist (hence 404)
        session.get.return_value.status_code = 404
        # Creation of the resource will be successful
        session.post.return_value = Mock(headers={'Location': '...'}, status_code=201)

        request_hapi_provider = BloombergBeapHapiRequestsProvider('https://api.bloomberg.com', session,
                                                                  'account_url', 'trigger_url', terminal_identity_user,
                                                                  terminal_identity_sn)
        self.data_provider.request_hapi_provider = request_hapi_provider

        fields_hapi_provider = Mock()
        fields_hapi_provider.get_fields_history_url.return_value = "fieldListURL", {}
        self.data_provider.fields_hapi_provider = fields_hapi_provider

        universe_provider = Mock()
        universe_provider.get_universe_url.return_value = "universeURL"
        self.data_provider.universe_hapi_provider = universe_provider

        return session

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider.datetime')
    def test_get_history__test_request_data_provider_payload_creation(self, mock_now):
        current_time = datetime(2025, 2, 7, 12, 34, 56)
        session = self.__test_payload_creation()
        mock_now.now.return_value = current_time
        mock_now.utcnow.return_value = current_time

        params = [
            (datetime(2025, 2, 6), datetime(2025, 2, 6), Frequency.DAILY, None, 'daily'),
            (datetime(2025, 2, 6), datetime(2026, 2, 6), Frequency.WEEKLY, None, 'weekly'),
            (datetime(2025, 2, 6), datetime(2026, 2, 6), Frequency.MONTHLY, "USD", 'monthly'),
            (datetime(2025, 2, 6), datetime(2026, 2, 6), Frequency.QUARTERLY, "CHF", 'quarterly'),
            (datetime(2025, 2, 6), datetime(2026, 2, 6), Frequency.YEARLY, "CAD", 'yearly'),
        ]

        for (start_date, end_date, frequency, currency, freq_string) in params:
            with self.subTest(start_date=start_date, end_date=end_date, frequency=frequency, freq_string=freq_string,
                              currency=currency):
                # Run the get history function
                self.data_provider.get_history(tickers=BloombergTicker("AAPL US Equity"), fields="PX_LAST",
                                               start_date=start_date, end_date=end_date,
                                               frequency=frequency, look_ahead_bias=True, currency=currency)

                expected_payload = {'@type': 'HistoryRequest',
                                    'description': 'Request History Payload used in creating fields component',
                                    'fieldList': 'fieldListURL',
                                    'formatting': {
                                        '@type': 'HistoryFormat',
                                        'dateFormat': 'yyyymmdd',
                                        'displayPricingSource': True,
                                        'fileType': 'unixFileType'},
                                    'identifier': f'hReq{current_time:%m%d%H%M%S%f}',
                                    'pricingSourceOptions': {
                                        '@type': 'HistoryPricingSourceOptions',
                                        'prefer': {'mnemonic': 'BGN'}
                                    },
                                    'runtimeOptions': {
                                        '@type': 'HistoryRuntimeOptions',
                                        'dateRange': {'@type': 'IntervalDateRange',
                                                      'endDate': f'{end_date:%Y-%m-%d}',
                                                      'startDate': f'{start_date:%Y-%m-%d}'},
                                        'period': freq_string},
                                    'title': 'Request History Payload',
                                    'trigger': 'trigger_url',
                                    'universe': 'universeURL'}
                if currency is not None:
                    expected_payload['runtimeOptions']['historyPriceCurrency'] = currency
                session.post.assert_called_with('requests/', json=expected_payload)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider.datetime')
    def test_get_history__test_correct_terminal_identity_user_within_payload(self, mock_now):
        current_time = datetime(2025, 2, 7, 12, 34, 56)
        session = self.__test_payload_creation("1234567890")
        mock_now.now.return_value = current_time
        mock_now.utcnow.return_value = current_time

        # Run the get history function
        self.data_provider.get_history(tickers=BloombergTicker("AAPL US Equity"), fields="PX_LAST",
                                       start_date=datetime(2025, 6, 2), end_date=datetime(2025, 6, 2),
                                       frequency=Frequency.DAILY, look_ahead_bias=True)

        expected_payload = {'@type': 'HistoryRequest',
                            'description': 'Request History Payload used in creating fields component',
                            'fieldList': 'fieldListURL',
                            'formatting': {
                                '@type': 'HistoryFormat',
                                'dateFormat': 'yyyymmdd',
                                'displayPricingSource': True,
                                'fileType': 'unixFileType'},
                            'identifier': f'hReq{current_time:%m%d%H%M%S%f}',
                            'pricingSourceOptions': {
                                '@type': 'HistoryPricingSourceOptions',
                                'prefer': {'mnemonic': 'BGN'}
                            },
                            'runtimeOptions': {
                                '@type': 'HistoryRuntimeOptions',
                                'dateRange': {'@type': 'IntervalDateRange',
                                              'endDate': '2025-06-02',
                                              'startDate': '2025-06-02'},
                                'period': 'daily'},
                            'title': 'Request History Payload',
                            'trigger': 'trigger_url',
                            'universe': 'universeURL',
                            'terminalIdentity': {
                                '@type': 'BbaTerminalIdentity',
                                'userNumber': 1234567890
                            }}

        session.post.assert_called_with('requests/', json=expected_payload)

    def test_get_history__incorrect_user_identity(self):
        with self.assertRaises(ValueError):
            self.__test_payload_creation(terminal_identity_user="234567890!")

    def test_get_history__incorrect_sn(self):
        with self.assertRaises(ValueError):
            self.__test_payload_creation(terminal_identity_user="234567890",
                                         terminal_identity_sn="123-123-w")

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider.datetime')
    def test_get_history__test_correct_terminal_identity_user_sn_within_payload(self, mock_now):
        current_time = datetime(2025, 2, 7, 12, 34, 56)
        session = self.__test_payload_creation("1234567890", "123-456")
        mock_now.now.return_value = current_time
        mock_now.utcnow.return_value = current_time

        # Run the get history function
        self.data_provider.get_history(tickers=BloombergTicker("AAPL US Equity"), fields="PX_LAST",
                                       start_date=datetime(2025, 6, 2), end_date=datetime(2025, 6, 2),
                                       frequency=Frequency.DAILY, look_ahead_bias=True)

        expected_payload = {'@type': 'HistoryRequest',
                            'description': 'Request History Payload used in creating fields component',
                            'fieldList': 'fieldListURL',
                            'formatting': {
                                '@type': 'HistoryFormat',
                                'dateFormat': 'yyyymmdd',
                                'displayPricingSource': True,
                                'fileType': 'unixFileType'},
                            'identifier': f'hReq{current_time:%m%d%H%M%S%f}',
                            'pricingSourceOptions': {
                                '@type': 'HistoryPricingSourceOptions',
                                'prefer': {'mnemonic': 'BGN'}
                            },
                            'runtimeOptions': {
                                '@type': 'HistoryRuntimeOptions',
                                'dateRange': {'@type': 'IntervalDateRange',
                                              'endDate': '2025-06-02',
                                              'startDate': '2025-06-02'},
                                'period': 'daily'},
                            'title': 'Request History Payload',
                            'trigger': 'trigger_url',
                            'universe': 'universeURL',
                            'terminalIdentity': {
                                '@type': 'BlpTerminalIdentity',
                                'userNumber': 1234567890,
                                'serialNumber': 123,
                                'workStation': 456
                            }}

        session.post.assert_called_with('requests/', json=expected_payload)
