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
plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.common.utils.dummy_ticker_mapper import DummyTickerMapper
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class SimpleMAStrategy(object):
    """
    strategy, which computes every day, before the market open time, two simple moving averages (long - 20 days,
    short - 5 days) and creates a buy order in case if the short moving average is greater or equal to the long moving
    average.
    """
    def __init__(self, ts: BacktestTradingSession, ticker: Ticker):
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.contract_ticker_mapper = ts.contract_ticker_mapper
        self.position_sizer = ts.position_sizer
        self.timer = ts.timer
        self.ticker = ticker

        # Subscribe to the BeforeMarketOpenEvent
        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        # Compute the moving averages
        long_ma_len = 20
        short_ma_len = 5

        # Use data handler to download last 20 daily close prices and use them to compute the moving averages
        long_ma_series = self.data_handler.historical_price(self.ticker,
                                                            PriceField.Close, long_ma_len)
        long_ma_price = long_ma_series.mean()

        short_ma_series = long_ma_series.tail(short_ma_len)
        short_ma_price = short_ma_series.mean()

        # Map the given ticker onto a Contract object, which can be further used to place an Order
        contract = self.contract_ticker_mapper.ticker_to_contract(self.ticker)

        if short_ma_price >= long_ma_price:
            # Place a buy Market Order, adjusting the position to a value equal to 100% of the portfolio
            orders = self.order_factory.target_percent_orders({contract: 1.0}, MarketOrder(), TimeInForce.DAY)
        else:
            orders = self.order_factory.target_percent_orders({contract: 0.0}, MarketOrder(), TimeInForce.DAY)

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
    session_builder.set_contract_ticker_mapper(DummyTickerMapper())

    ts = session_builder.build(start_date, end_date)

    SimpleMAStrategy(ts, ticker)
    ts.start_trading()


if __name__ == "__main__":
    main()
