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
from unittest import TestCase

import pandas as pd

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_same_index, assert_series_equal
from qf_lib.tests.integration_tests.connect_to_data_provider import get_data_provider


class TestBloombergDataProvider(TestCase):
    """Class which tests look_ahead_bias flag with Bloomberg Data Provider."""

    def setUp(self) -> None:
        try:
            self.timer = SettableTimer()
            self.bbg_provider = get_data_provider(self.timer)
            self.bbg_provider.frequency = Frequency.DAILY
            MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
            MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

        except Exception as e:
            raise self.skipTest(e)

    def test_market_open_price_before_market_open(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 1))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                             datetime(2022, 4, 24), datetime(2022, 4, 26))

        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 25), PriceField.Open]))
        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 25), PriceField.Close]))

        self.assertEqual(prices.index[-1], datetime(2022, 4, 25))

    def test_market_open_price_before_market_open__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 1))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.Open,
                                             datetime(2022, 4, 26),
                                             datetime(2022, 4, 26))
        self.assertFalse(is_finite_number(prices))

    def test_market_open_price_before_market_close__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 15))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                             datetime(2022, 4, 26), datetime(2022, 4, 26))
        self.assertTrue(all(prices.isna()))

        self.timer.set_current_time(datetime(2022, 4, 29, 15))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                             datetime(2022, 4, 29), datetime(2022, 4, 30))
        self.assertTrue(prices.empty)

    def test_market_open_price_after_market_close__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 23))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                             datetime(2022, 4, 26), datetime(2022, 4, 26))
        self.assertTrue(is_finite_number(prices.loc[PriceField.Open]))
        self.assertTrue(is_finite_number(prices.loc[PriceField.Close]))

    def test_market_open_price_before_market_close(self):
        """Test if the Open price is returned in case if current time is after market open
        and before market close on the end_date day. The low, high, close prices and volume
        should be set to Nan. """

        self.timer.set_current_time(datetime(2022, 4, 26, 15))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                             datetime(2022, 4, 25), datetime(2022, 4, 26))

        self.assertEqual(prices.index[-1], datetime(2022, 4, 25))
        self.assertEqual(type(prices), PricesDataFrame)

    def test_market_open_price_after_market_close(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 23))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                             datetime(2022, 4, 25), datetime(2022, 4, 26))

        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 26), PriceField.Open]))
        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 26), PriceField.Close]))

        self.assertEqual(prices.index[-1], datetime(2022, 4, 26))

    def test_market_open_price_after_market_close_before_end_date(self):
        """Test if the Open price is returned in case if the current time is after market open
        but before end_date. """

        self.timer.set_current_time(datetime(2022, 4, 26, 15))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                             datetime(2022, 4, 25), datetime(2022, 4, 30))
        self.assertEqual(prices.index[-1], datetime(2022, 4, 25))
        self.assertEqual(type(prices), PricesDataFrame)

    def test_day_without_data__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 30, 15))
        prices = self.bbg_provider.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                             datetime(2022, 4, 30), datetime(2022, 4, 30))
        self.assertFalse(is_finite_number(prices.loc[PriceField.Open]))
        self.assertFalse(is_finite_number(prices.loc[PriceField.Close]))

    def test_get_price_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(datetime(2018, 2, 12))
        prices_tms = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.Close, datetime(2018, 1, 2),
                                                 datetime(2018, 1, 31))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 31), prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(
            datetime(2018, 1, 31) + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.Close, datetime(2018, 1, 2),
                                                 datetime(2018, 1, 31))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 31), prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        close_prices_tms = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.Close,
                                                       datetime(2018, 1, 2),
                                                       datetime(2018, 1, 31))

        self.assertEqual(datetime(2018, 1, 2), close_prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), close_prices_tms.index[-1].to_pydatetime())

    def test_get_open_price_when_end_date_is_today_before_market_close__single_ticker(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        open_prices_tms = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.Open,
                                                      datetime(2018, 1, 2))

        self.assertEqual(datetime(2018, 1, 2), open_prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), open_prices_tms.index[-1].to_pydatetime())

    def test_get_open_price_when_end_date_is_today_before_market_close__multiple_tickers(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        tickers = [BloombergTicker("SPX Index"), BloombergTicker("MSFT US Equity")]
        open_prices_tms = self.bbg_provider.get_price(tickers, PriceField.Open, datetime(2018, 1, 2), self.timer.now())

        self.assertEqual(datetime(2018, 1, 2), open_prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), open_prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(
            datetime(2018, 1, 30) + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.bbg_provider.get_price(BloombergTicker("SPX Index"), PriceField.Close, datetime(2018, 1, 2),
                                                 datetime(2018, 1, 30))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), prices_tms.index[-1].to_pydatetime())

    def test_get_last_price_single_ticker(self):
        with self.subTest("Test if getting single ticker value works, when a single ticker is passed"):
            self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() +
                                        RelativeDelta(hours=1))
            single_price = self.bbg_provider.get_last_available_price(BloombergTicker("SPX Index"))
            self.assertTrue(isinstance(single_price, float))

        with self.subTest("Test at market open"):
            self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time())
            at_market_open = self.bbg_provider.get_last_available_price([BloombergTicker("SPX Index")])

            self.assertEqual(BloombergTicker("SPX Index"), at_market_open.index[0])
            self.assertEqual(single_price, at_market_open[0])

        with self.subTest("Test during the trading session"):
            self.timer.set_current_time(
                datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
            during_the_day_last_prices = self.bbg_provider.get_last_available_price([BloombergTicker("SPX Index")])

            self.assertEqual(BloombergTicker("SPX Index"), during_the_day_last_prices.index[0])
            self.assertEqual(single_price, during_the_day_last_prices[0])

        with self.subTest("Test after the trading session"):
            self.timer.set_current_time(
                datetime(2018, 1, 31) + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
            after_close_last_prices = self.bbg_provider.get_last_available_price([BloombergTicker("SPX Index")])

            self.assertEqual(BloombergTicker("SPX Index"), after_close_last_prices.index[0])
            self.assertNotEqual(during_the_day_last_prices[0], after_close_last_prices[0])

        with self.subTest("Test before the trading session"):
            self.timer.set_current_time(
                datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() - RelativeDelta(hours=1))
            before_trading_session_prices = self.bbg_provider.get_last_available_price([BloombergTicker("SPX Index")])

            self.assertEqual(BloombergTicker("SPX Index"), before_trading_session_prices.index[0])
            self.assertNotEqual(during_the_day_last_prices[0], before_trading_session_prices[0])
            self.assertNotEqual(after_close_last_prices[0], before_trading_session_prices[0])

    def test_get_last_price_with_multiple_tickers_when_current_data_is_unavailable(self):
        self.timer.set_current_time(datetime(2018, 1, 1) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        last_prices = self.bbg_provider.get_last_available_price(
            [BloombergTicker("SPX Index"), BloombergTicker("GOOGL US Equity")])

        self.assertEqual(BloombergTicker("SPX Index"), last_prices.index[0])
        self.assertEqual(BloombergTicker("GOOGL US Equity"), last_prices.index[1])

    def test_get_last_price_with_empty_tickers_list(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        last_prices = self.bbg_provider.get_last_available_price([])
        assert_series_equal(PricesSeries(), last_prices)

    def test_get_history_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(datetime(2018, 2, 12))
        prices_tms = self.bbg_provider.get_history(BloombergTicker("SPX Index"), "PX_TO_BOOK_RATIO",
                                                   datetime(2018, 1, 2), datetime(2018, 1, 31))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 31), prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(
            datetime(2018, 1, 31) + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.bbg_provider.get_history(BloombergTicker("SPX Index"), "PX_TO_BOOK_RATIO",
                                                   datetime(2018, 1, 2), datetime(2018, 1, 31))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 31), prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.bbg_provider.get_history(BloombergTicker("SPX Index"), "PX_TO_BOOK_RATIO",
                                                   datetime(2018, 1, 2), datetime(2018, 1, 31))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(
            datetime(2018, 1, 30) + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.bbg_provider.get_history(BloombergTicker("SPX Index"), "PX_TO_BOOK_RATIO",
                                                   datetime(2018, 1, 2), datetime(2018, 1, 30))

        self.assertEqual(datetime(2018, 1, 2), prices_tms.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), prices_tms.index[-1].to_pydatetime())

    def test_get_history_with_multiple_tickers(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        resilt_df = self.bbg_provider.get_history(
            [BloombergTicker("MSFT US Equity"), BloombergTicker("GOOGL US Equity")], "PX_TO_BOOK_RATIO",
            datetime(2018, 1, 2), datetime(2018, 1, 30))

        self.assertEqual(BloombergTicker("MSFT US Equity"), resilt_df.columns[0])
        self.assertEqual(BloombergTicker("GOOGL US Equity"), resilt_df.columns[1])
        self.assertEqual(datetime(2018, 1, 2), resilt_df.index[0].to_pydatetime())
        self.assertEqual(datetime(2018, 1, 30), resilt_df.index[-1].to_pydatetime())
        self.assertEqual(resilt_df.shape, (20, 2))

    def test_historical_price_many_tickers_many_fields(self):
        self.timer.set_current_time(datetime(2018, 1, 31) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        result_array = self.bbg_provider.historical_price([BloombergTicker("MSFT US Equity")],
                                                          [PriceField.Open, PriceField.Close],
                                                          nr_of_bars=5)

        self.assertEqual(QFDataArray, type(result_array))
        self.assertEqual((5, 1, 2), result_array.shape)

        expected_dates_str = ["2018-01-24", "2018-01-25", "2018-01-26", "2018-01-29", "2018-01-30"]
        expected_dates = [str_to_date(date_str) for date_str in expected_dates_str]
        assert_same_index(pd.DatetimeIndex(expected_dates, name=DATES), result_array.dates.to_index(),
                          check_index_type=True, check_names=True)

    def test_historical_price_many_tickers_one_field(self):
        self.timer.set_current_time(datetime(2018, 1, 4) + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        result_df = self.bbg_provider.historical_price([BloombergTicker("MSFT US Equity")], PriceField.Open,
                                                       nr_of_bars=5)

        self.assertEqual(PricesDataFrame, type(result_df))

        expected_dates_idx = pd.DatetimeIndex(
            ['2017-12-27', '2017-12-28', '2017-12-29', '2018-01-02', '2018-01-03'], name=DATES
        )
        assert_same_index(expected_dates_idx, result_df.index, check_index_type=True, check_names=True)

        expected_tickers_idx = pd.Index([BloombergTicker("MSFT US Equity")], name=TICKERS)
        assert_same_index(expected_tickers_idx, result_df.columns, check_index_type=True, check_names=True)
