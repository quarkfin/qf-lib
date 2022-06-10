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

from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.tests.integration_tests.connect_to_data_provider import get_data_provider


class TestBloombergDataHandler(TestCase):
    """Class which tests Data Handler encapsulation with Bloomberg Data Provider."""

    def setUp(self) -> None:
        try:
            bbg_provider = get_data_provider()
            self.timer = SettableTimer()
            self.daily_data_handler = DailyDataHandler(bbg_provider, self.timer)

            MarketOpenEvent.set_trigger_time({"hour": 8, "minute": 30, "second": 0, "microsecond": 0})
            MarketCloseEvent.set_trigger_time({"hour": 16, "minute": 0, "second": 0, "microsecond": 0})

        except Exception as e:
            raise self.skipTest(e)

    def test_market_open_price_before_market_open(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 1))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                                   datetime(2022, 4, 24), datetime(2022, 4, 26))

        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 25), PriceField.Open]))
        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 25), PriceField.Close]))

        self.assertEqual(prices.index[-1], datetime(2022, 4, 25))

    def test_market_open_price_before_market_open__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 1))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), PriceField.Open,
                                                   datetime(2022, 4, 26), datetime(2022, 4, 26))
        self.assertFalse(is_finite_number(prices))

    def test_market_open_price_before_market_close__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 15))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                                   datetime(2022, 4, 26), datetime(2022, 4, 26))
        self.assertTrue(all(prices.isna()))

        self.timer.set_current_time(datetime(2022, 4, 29, 15))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                                   datetime(2022, 4, 29), datetime(2022, 4, 30))
        self.assertTrue(prices.empty)

    def test_market_open_price_after_market_close__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 23))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                                   datetime(2022, 4, 26), datetime(2022, 4, 26))
        self.assertTrue(is_finite_number(prices.loc[PriceField.Open]))
        self.assertTrue(is_finite_number(prices.loc[PriceField.Close]))

    def test_market_open_price_before_market_close(self):
        """Test if the Open price is returned in case if current time is after market open
        and before market close on the end_date day. The low, high, close prices and volume
        should be set to Nan. """

        self.timer.set_current_time(datetime(2022, 4, 26, 15))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                                   datetime(2022, 4, 25), datetime(2022, 4, 26))

        self.assertEqual(prices.index[-1], datetime(2022, 4, 25))
        self.assertEqual(type(prices), PricesDataFrame)

    def test_market_open_price_after_market_close(self):
        self.timer.set_current_time(datetime(2022, 4, 26, 23))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                                   datetime(2022, 4, 25), datetime(2022, 4, 26))

        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 26), PriceField.Open]))
        self.assertTrue(is_finite_number(prices.loc[datetime(2022, 4, 26), PriceField.Close]))

        self.assertEqual(prices.index[-1], datetime(2022, 4, 26))

    def test_market_open_price_after_market_close_before_end_date(self):
        """Test if the Open price is returned in case if the current time is after market open
        but before end_date. """

        self.timer.set_current_time(datetime(2022, 4, 26, 15))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), PriceField.ohlcv(),
                                                   datetime(2022, 4, 25), datetime(2022, 4, 30))
        self.assertEqual(prices.index[-1], datetime(2022, 4, 25))
        self.assertEqual(type(prices), PricesDataFrame)

    def test_day_without_data__single_date(self):
        self.timer.set_current_time(datetime(2022, 4, 30, 15))
        prices = self.daily_data_handler.get_price(BloombergTicker("SPX Index"), [PriceField.Open, PriceField.Close],
                                                   datetime(2022, 4, 30), datetime(2022, 4, 30))
        self.assertFalse(is_finite_number(prices.loc[PriceField.Open]))
        self.assertFalse(is_finite_number(prices.loc[PriceField.Close]))
