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
from unittest import TestCase
from unittest.mock import patch

from numpy import isnan, nan
from pandas import date_range

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal


class TestDataProvider(TestCase):

    @classmethod
    @patch.multiple(DataProvider, __abstractmethods__=set())
    def setUpClass(cls) -> None:
        cls.ticker_1 = BloombergTicker("Example Index")
        cls.ticker_2 = BloombergTicker("Example Comdty")

        cls.data_provider = DataProvider()

    def setUp(self) -> None:
        self.current_time = None

        datetime_patcher = patch('qf_lib.data_providers.data_provider.datetime')
        datetime_mock = datetime_patcher.start()
        datetime_mock.now.side_effect = lambda: self.current_time
        self.addCleanup(datetime_patcher.stop)

        get_price_patcher = patch.object(DataProvider, 'get_price')
        mocked_get_price = get_price_patcher.start()
        mocked_get_price.side_effect = self._mock_get_price
        self.addCleanup(get_price_patcher.stop)

    def test_get_last_available_price__before_data_starts__daily(self):
        # Check if the correct output is returned in case if a single ticker is provided
        self._assert_last_price_is_correct("2021-04-30 00:00:00.000000", self.ticker_1, nan, Frequency.DAILY)
        self._assert_last_price_is_correct("2021-04-30 00:00:00.000000", self.ticker_2, nan, Frequency.DAILY)

        # Check if the correct output is returned in case if a list of tickers is provided
        self._assert_last_prices_are_correct("2021-04-30 00:00:00.000000", [nan, nan], Frequency.DAILY)
        self._assert_last_prices_are_correct("2021-05-06 00:00:00.000000", [25.0, 27.0], Frequency.DAILY)

    def test_get_last_available_price__data_available_for_every_ticker__daily(self):
        # Check if the correct output is returned in case if a single ticker is provided
        self._assert_last_price_is_correct("2021-05-01 00:00:00.000000", self.ticker_1, 26, Frequency.DAILY)
        self._assert_last_price_is_correct("2021-05-01 00:00:00.000000", self.ticker_2, 28, Frequency.DAILY)

        self._assert_last_price_is_correct("2021-05-05 00:00:00.000000", self.ticker_1, 25, Frequency.DAILY)
        self._assert_last_price_is_correct("2021-05-05 00:00:00.000000", self.ticker_2, 27, Frequency.DAILY)

        # Check if the correct output is returned in case if a list of tickers is provided
        self._assert_last_prices_are_correct("2021-05-01 00:00:00.000000", [26, 28], Frequency.DAILY)
        self._assert_last_prices_are_correct("2021-05-05 14:30:00.000000", [25.0, 27.0], Frequency.DAILY)

    def test_get_last_available_price__data_available_for_the_first_ticker__daily(self):
        # Check if the correct output is returned in case if a single ticker is provided
        self._assert_last_price_is_correct("2021-05-03 00:00:00.000000", self.ticker_1, 32, Frequency.DAILY)
        self._assert_last_price_is_correct("2021-05-03 00:00:00.000000", self.ticker_2, 30, Frequency.DAILY)

        self._assert_last_price_is_correct("2021-05-04 00:00:00.000000", self.ticker_1, 31, Frequency.DAILY)
        self._assert_last_price_is_correct("2021-05-04 00:00:00.000000", self.ticker_2, 30, Frequency.DAILY)

        # Check if the correct output is returned in case if a list of tickers is provided
        self._assert_last_prices_are_correct("2021-05-03 13:30:00.000000", [32.0, 30.0], Frequency.DAILY)
        self._assert_last_prices_are_correct("2021-05-04 13:30:00.000000", [31.0, 30.0], Frequency.DAILY)

    def test_get_last_available_price__data_available_for_the_second_ticker__daily(self):
        # Check if the correct output is returned in case if a single ticker is provided
        self._assert_last_price_is_correct("2021-05-02 00:00:00.000000", self.ticker_1, 26, Frequency.DAILY)
        self._assert_last_price_is_correct("2021-05-02 00:00:00.000000", self.ticker_2, 30, Frequency.DAILY)

        # Check if the correct output is returned in case if a list of tickers is provided
        self._assert_last_prices_are_correct("2021-05-02 13:30:00.000000", [26.0, 30.0], Frequency.DAILY)

    def test_historical_price__negative_number_of_bars__daily(self):
        # Check if the correct output is returned in case if a single ticker is provided
        self.current_time = str_to_date("2021-05-03 00:00:00.000000", DateFormat.FULL_ISO)
        with self.assertRaises(AssertionError):
            self.data_provider.historical_price(self.ticker_1, PriceField.Open, 0, frequency=Frequency.DAILY)
            self.data_provider.historical_price(self.ticker_1, PriceField.Open, -2, frequency=Frequency.DAILY)
            self.data_provider.historical_price([self.ticker_1, self.ticker_2], PriceField.Open, -1,
                                                frequency=Frequency.DAILY)

    def test_historical_price__before_data_starts__daily(self):
        self.current_time = str_to_date("2021-04-30 00:00:00.000000", DateFormat.FULL_ISO)

        with self.assertRaises(ValueError):
            self.data_provider.historical_price(self.ticker_2, PriceField.Open, 2, frequency=Frequency.DAILY)
            self.data_provider.historical_price([self.ticker_1, self.ticker_2], PriceField.ohlcv(), 1,
                                                frequency=Frequency.DAILY)

    def test_historical_price__single_ticker__single_field__daily(self):
        self.current_time = str_to_date("2021-05-03 00:00:00.000000", DateFormat.FULL_ISO)

        # Test when the current day does not have the open price
        actual_series = self.data_provider.historical_price(self.ticker_2, PriceField.Open, 2,
                                                            frequency=Frequency.DAILY)
        expected_series = PricesSeries(data=[27, 29], index=[str_to_date('2021-05-01'), str_to_date('2021-05-02')])
        assert_series_equal(actual_series, expected_series, check_names=False)

        # Test when the previous day does not have the open price
        actual_series = self.data_provider.historical_price(self.ticker_1, PriceField.Open, 2,
                                                            frequency=Frequency.DAILY)
        expected_series = PricesSeries(data=[25, 31], index=[str_to_date('2021-05-01'), str_to_date('2021-05-03')])
        assert_series_equal(actual_series, expected_series, check_names=False)

    def test_historical_price__single_ticker__multiple_fields__daily(self):
        self.current_time = str_to_date("2021-05-06 00:00:00.000000", DateFormat.FULL_ISO)

        # Test when the current day does not have the open price
        actual_bars = self.data_provider.historical_price(self.ticker_2, PriceField.ohlcv(), 2,
                                                          frequency=Frequency.DAILY)
        expected_bars = PricesDataFrame(data=[[29.0, 29.1, 29.2, 30.0, 29.3],
                                              [27.0, 27.1, 27.2, None, 27.3]],
                                        index=[str_to_date('2021-05-02'), str_to_date('2021-05-05')],
                                        columns=PriceField.ohlcv())
        assert_dataframes_equal(expected_bars, actual_bars, check_names=False)

        self.current_time = str_to_date("2021-05-06 00:00:00.000000", DateFormat.FULL_ISO)

        actual_bars = self.data_provider.historical_price(self.ticker_2, PriceField.ohlcv(), 3,
                                                          frequency=Frequency.DAILY)
        expected_bars = PricesDataFrame(data=[[27.0, 27.1, 27.2, 28.0, 27.3],
                                              [29.0, 29.1, 29.2, 30.0, 29.3],
                                              [27.0, 27.1, 27.2, None, 27.3]],
                                        index=[str_to_date('2021-05-01'), str_to_date('2021-05-02'),
                                               str_to_date('2021-05-05')],
                                        columns=PriceField.ohlcv())
        assert_dataframes_equal(expected_bars, actual_bars, check_names=False)

        # More than 3 bars are not available
        with self.assertRaises(ValueError):
            self.data_provider.historical_price(self.ticker_2, PriceField.ohlcv(), 4, frequency=Frequency.DAILY)

    def test_historical_price__multiple_tickers__multiple_fields__daily(self):
        self.current_time = str_to_date("2021-05-06 00:00:00.000000", DateFormat.FULL_ISO)

        # Test when the current day does not have the open price
        actual_bars = self.data_provider.historical_price([self.ticker_1, self.ticker_2], PriceField.ohlcv(), 2,
                                                          frequency=Frequency.DAILY)
        self.assertEqual(type(actual_bars), QFDataArray)
        assert_series_equal(actual_bars.dates.to_pandas(), date_range('2021-05-04', '2021-05-05', freq="D").to_series(),
                            check_names=False)

    def test_historical_price__margin_adjustment__daily(self):
        # In case if we want only 1 historical bar and the last full bar was more than ~12 days ago, the adjustment of
        # the margin for the "number of days to go back" need to be performed
        self.current_time = str_to_date("2021-05-18 00:00:00.000000", DateFormat.FULL_ISO)
        actual_bars = self.data_provider.historical_price(self.ticker_1, PriceField.ohlcv(), 1,
                                                          frequency=Frequency.DAILY)
        expected_bars = PricesDataFrame(data=[[25.0, 25.1, 25.2, None, 25.3]], index=[str_to_date('2021-05-05')],
                                        columns=PriceField.ohlcv())
        assert_dataframes_equal(actual_bars, expected_bars, check_names=False)

        self.current_time = str_to_date("2021-05-27 00:00:00.000000", DateFormat.FULL_ISO)
        actual_bars = self.data_provider.historical_price(self.ticker_1, PriceField.ohlcv(), 1,
                                                          frequency=Frequency.DAILY)
        assert_dataframes_equal(actual_bars, expected_bars, check_names=False)

        with self.assertRaises(ValueError):
            self.current_time = str_to_date("2021-06-06 00:00:00.000000", DateFormat.FULL_ISO)
            self.data_provider.historical_price(self.ticker_1, PriceField.ohlcv(), 1, frequency=Frequency.DAILY)

    def _assert_last_prices_are_correct(self, curr_time_str, expected_values, frequency):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.current_time = current_time
        expected_series = PricesSeries(data=expected_values, index=[self.ticker_1, self.ticker_2])
        actual_series = self.data_provider.get_last_available_price([self.ticker_1, self.ticker_2], frequency)
        assert_series_equal(expected_series, actual_series, check_names=False)

    def _assert_last_price_is_correct(self, curr_time_str, ticker, expected_value, frequency):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.current_time = current_time
        actual_value = self.data_provider.get_last_available_price(ticker, frequency)
        if isnan(expected_value):
            self.assertTrue(isnan(actual_value))
        else:
            self.assertEqual(expected_value, actual_value)

    def _mock_get_price(self, tickers, fields, start_date, end_date, frequency):
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, PriceField)

        mock_daily_data = QFDataArray.create(
            dates=date_range(start='2021-05-01', end='2021-05-06', freq='D'),
            tickers=[self.ticker_1, self.ticker_2],
            fields=PriceField.ohlcv(),
            data=[
                # 2021-05-01
                [
                    # Open High  Low   Close Volume
                    [25.0, 25.1, 25.2, 26.0, 25.3],  # TICKER 1
                    [27.0, 27.1, 27.2, 28.0, 27.3]  # TICKER 2
                ],
                # 2021-05-02
                [
                    # Open High  Low   Close Volume
                    [None, None, None, None, None],  # TICKER 1
                    [29.0, 29.1, 29.2, 30.0, 29.3]  # TICKER 2
                ],
                # 2021-05-03
                [
                    # Open High  Low   Close Volume
                    [31.0, 31.1, 31.2, 32.0, 31.3],  # TICKER 1
                    [None, None, None, None, None]  # TICKER 2
                ],
                # 2021-05-04
                [
                    # Open High  Low   Close Volume
                    [31.0, None, None, None, None],  # TICKER 1
                    [None, None, None, None, None]  # TICKER 2
                ],
                # 2021-05-05
                [
                    # Open High  Low   Close Volume
                    [25.0, 25.1, 25.2, None, 25.3],  # TICKER 1
                    [27.0, 27.1, 27.2, None, 27.3]  # TICKER 2
                ],
                # 2021-05-06
                [
                    # Open High  Low   Close Volume
                    [None, None, None, None, None],  # TICKER 1
                    [None, None, None, None, None]  # TICKER 2
                ],
            ]
        )

        mock_intraday_data = QFDataArray.create(
            dates=date_range(start='2021-05-01', end='2021-05-06', freq='D'),
            tickers=[self.ticker_1, self.ticker_2],
            fields=PriceField.ohlcv(),
            data=[
                # 2021-05-01
                [
                    # Open High  Low   Close Volume
                    [25.0, 25.1, 25.2, 26.0, 25.3],  # TICKER 1
                    [27.0, 27.1, 27.2, 28.0, 27.3]  # TICKER 2
                ],
                # 2021-05-02
                [
                    # Open High  Low   Close Volume
                    [None, None, None, None, None],  # TICKER 1
                    [29.0, 29.1, 29.2, 30.0, 29.3]  # TICKER 2
                ],
                # 2021-05-03
                [
                    # Open High  Low   Close Volume
                    [31.0, 31.1, 31.2, 32.0, 31.3],  # TICKER 1
                    [None, None, None, None, None]  # TICKER 2
                ],
                # 2021-05-04
                [
                    # Open High  Low   Close Volume
                    [31.0, None, None, None, None],  # TICKER 1
                    [None, None, None, None, None]  # TICKER 2
                ],
                # 2021-05-05
                [
                    # Open High  Low   Close Volume
                    [25.0, 25.1, 25.2, None, 25.3],  # TICKER 1
                    [27.0, 27.1, 27.2, None, 27.3]  # TICKER 2
                ],
                # 2021-05-06
                [
                    # Open High  Low   Close Volume
                    [None, None, None, None, None],  # TICKER 1
                    [None, None, None, None, None]  # TICKER 2
                ],
            ]
        )

        data = mock_daily_data.loc[start_date:end_date, tickers, fields] if frequency == Frequency.DAILY else \
            mock_intraday_data.loc[start_date:end_date, tickers, fields]
        return normalize_data_array(data, tickers, fields, False, got_single_ticker, got_single_field, True)
