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

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.enums.price_field import PriceField
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class SimpleMAStrategy(object):
    """
    A testing strategy that simply purchases (longs) an asset as soon as it starts and then holds until the completion
    of a backtest.
    """

    ticker = BloombergTicker("MSFT US Equity")

    def __init__(self, ts: BacktestTradingSession):
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.contract_ticker_mapper = ts.contract_ticker_mapper
        self.position_sizer = ts.position_sizer
        self.timer = ts.timer

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        long_ma_len = 20
        short_ma_len = 5

        long_ma_series = self.data_handler.historical_price(self.ticker, PriceField.Close, long_ma_len)
        long_ma_price = long_ma_series.mean()

        short_ma_series = long_ma_series.tail(short_ma_len)
        short_ma_price = short_ma_series.mean()

        contract = self.contract_ticker_mapper.ticker_to_contract(self.ticker)

        if short_ma_price >= long_ma_price:
            orders = self.order_factory.target_percent_orders({contract: 1.0}, MarketOrder(), TimeInForce.GTC)
        else:
            orders = self.order_factory.target_percent_orders({contract: 0.0}, MarketOrder(), TimeInForce.GTC)

        self.broker.cancel_all_open_orders()
        self.broker.place_orders(orders)


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2011-01-01")

    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_backtest_name('Simple_MA')
    session_builder.set_initial_cash(1000000)
    session_builder.set_frequency(Frequency.DAILY)
    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(SimpleMAStrategy.ticker, RelativeDelta(days=40))

    SimpleMAStrategy(ts)
    ts.start_trading()

    actual_end_value = ts.portfolio.portfolio_eod_series()[-1]
    expected_value = 898294.64

    print("Expected End Value = {}".format(expected_value))
    print("Actual End Value   = {}".format(actual_end_value))
    print("DIFF               = {}".format(expected_value - actual_end_value))

    test = TestCase()
    test.assertAlmostEqual(expected_value, actual_end_value, places=2)


if __name__ == "__main__":
    main()
