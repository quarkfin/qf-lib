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
import os
import unittest
from unittest import TestCase

import matplotlib

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.miscellaneous.get_cached_value import CachedValueException, cached_value
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_series_equal
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

matplotlib.use("Agg")

from qf_lib_tests.integration_tests.backtesting.trading_session_for_tests import TestingTradingSession
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.common.enums.price_field import PriceField
from qf_lib.data_providers.bloomberg import BloombergDataProvider

from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class BuyAndHoldStrategy(object):
    """
    A testing strategy that simply purchases (longs) an asset as soon as it starts and then holds until the completion
    of a backtest.
    """
    MICROSOFT_CONTRACT = Contract(symbol="MSFT US Equity", security_type='STK', exchange='NASDAQ')
    MICROSOFT_TICKER = BloombergTicker("MSFT US Equity")

    def __init__(self, broker: Broker, order_factory: OrderFactory, scheduler: Scheduler):
        self.order_factory = order_factory
        self.broker = broker

        self.invested = False

        scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        if not self.invested:
            orders = self.order_factory.value_orders({self.MICROSOFT_CONTRACT: self.broker.get_portfolio_value()},
                                                     MarketOrder(), TimeInForce.OPG)
            self.broker.place_orders(orders)
            self.invested = True


settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not os.path.exists('Bloomberg_intraday_frequency_1_get_price.cache') and
                 not bbg_provider.connected, "No data available")
class TestBacktester(TestCase):

    @classmethod
    def setUpDataProvider(cls, start_date, end_date):

        # configure the data provider
        input_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(input_dir, 'Bloomberg_intraday_frequency_1_get_price.cache')

        def get_data_provider():
            if bbg_provider.connected:
                # Load the data with 1 minute frequency
                return bbg_provider.get_price([BuyAndHoldStrategy.MICROSOFT_TICKER],
                                              PriceField.ohlcv(),
                                              start_date,
                                              end_date, Frequency.MIN_1)
            else:
                raise CachedValueException

        prefetched_data = cached_value(get_data_provider, filepath)

        return PresetDataProvider(prefetched_data, start_date, end_date, Frequency.MIN_1) if \
            prefetched_data is not None else None

    def test_backtester_with_buy_and_hold_strategy(self):
        start_date = str_to_date("2019-07-16")
        end_date = str_to_date("2019-09-01")
        data_provider = self.setUpDataProvider(str_to_date("2019-07-01"), str_to_date("2019-09-01"))

        msft_prices = data_provider.get_price(
            BuyAndHoldStrategy.MICROSOFT_TICKER, fields=[PriceField.Open, PriceField.Close],
            start_date=start_date, end_date=end_date, frequency=Frequency.MIN_1
        )

        initial_cash = msft_prices.loc[start_date + MarketOpenEvent.trigger_time(), PriceField.Open]
        ts = TestingTradingSession(data_provider, start_date, end_date, initial_cash)

        BuyAndHoldStrategy(ts.broker, ts.order_factory, ts.notifiers.scheduler)

        # Set up the backtest
        ts.start_trading()

        actual_portfolio_tms = ts.portfolio.get_portfolio_eod_tms()

        expected_portfolio_tms = msft_prices.loc[:, PriceField.Close].asof(actual_portfolio_tms.index)
        expected_portfolio_tms[:-1] = expected_portfolio_tms[1:]
        assert_series_equal(expected_portfolio_tms, actual_portfolio_tms, check_names=False)


if __name__ == "__main__":
    unittest.main()
