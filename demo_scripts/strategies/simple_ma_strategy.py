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
import matplotlib.pyplot as plt

from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
    CalculateAndPlaceOrdersRegularEvent
from qf_lib.backtesting.strategies.abstract_strategy import AbstractStrategy

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class SimpleMAStrategy(AbstractStrategy):
    """
    strategy, which computes every day, before the market open time, two simple moving averages (long - 20 days,
    short - 5 days) and creates a buy order in case if the short moving average is greater or equal to the long moving
    average.
    """
    def __init__(self, ts: BacktestTradingSession, ticker: Ticker):
        super().__init__(ts)
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.ticker = ticker

    def calculate_and_place_orders(self):
        # Compute the moving averages
        long_ma_len = 20
        short_ma_len = 5

        # Use data handler to download last 20 daily close prices and use them to compute the moving averages
        long_ma_series = self.data_handler.historical_price(self.ticker, PriceField.Close, long_ma_len)
        long_ma_price = long_ma_series.mean()

        short_ma_series = long_ma_series.tail(short_ma_len)
        short_ma_price = short_ma_series.mean()

        if short_ma_price >= long_ma_price:
            # Place a buy Market Order, adjusting the position to a value equal to 100% of the portfolio
            orders = self.order_factory.target_percent_orders({self.ticker: 1.0}, MarketOrder(), TimeInForce.DAY)
        else:
            orders = self.order_factory.target_percent_orders({self.ticker: 0.0}, MarketOrder(), TimeInForce.DAY)

        # Cancel any open orders and place the newly created ones
        self.broker.cancel_all_open_orders()
        self.broker.place_orders(orders)


def main():
    # settings
    backtest_name = 'Simple MA Strategy Demo'
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2015-03-01")
    ticker = DummyTicker("AAA")

    # configuration
    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_frequency(Frequency.DAILY)
    session_builder.set_backtest_name(backtest_name)
    session_builder.set_data_provider(daily_data_provider)

    ts = session_builder.build(start_date, end_date)

    strategy = SimpleMAStrategy(ts, ticker)
    CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
    CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
    strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

    ts.start_trading()


if __name__ == "__main__":
    main()
