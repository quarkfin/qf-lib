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
import logging

import matplotlib.pyplot as plt

from qf_lib.backtesting.events.time_event.periodic_event.periodic_event import PeriodicEvent
from qf_lib.backtesting.strategies.abstract_strategy import AbstractStrategy
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import intraday_data_provider
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class OnNewBarEvent(PeriodicEvent):
    def notify(self, listener) -> None:
        listener.on_new_bar(self)


class OnNewBarSignalGeneration:
    """ Wrapper, which facilitates the subscription process of the Strategy to the OnNewBarEvent. """
    def __init__(self, strategy: AbstractStrategy):
        self.strategy = strategy
        self.timer = strategy.timer
        strategy.notifiers.scheduler.subscribe(OnNewBarEvent, listener=self)

    def on_new_bar(self, _: OnNewBarEvent):
        if self.timer.now().weekday() not in (5, 6):  # Skip saturdays and sundays
            self.strategy.calculate_and_place_orders()


class IntradayMAStrategy(AbstractStrategy):
    """
    Strategy which computes two simple moving averages (long - 20 minutes, short - 5 minutes) every 15 minutes, between
    10:00 and 13:00, and creates a buy order in case if the short moving average is greater or equal to the long moving
    average.
    """
    def __init__(self, ts: BacktestTradingSession, ticker: Ticker):
        super().__init__(ts)
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.position_sizer = ts.position_sizer
        self.timer = ts.timer
        self.ticker = ticker

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def calculate_and_place_orders(self):
        self.logger.info("{} - Computing signals".format(self.timer.now()))

        # Compute the moving averages
        long_ma_len = 20
        short_ma_len = 5

        # Use data handler to download last 20 daily close prices and use them to compute the moving averages
        long_ma_series = self.data_handler.historical_price(self.ticker, PriceField.Close, long_ma_len,
                                                            frequency=Frequency.MIN_1)
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
    backtest_name = 'Intraday MA Strategy Demo'
    start_date = str_to_date("2019-07-01")
    end_date = str_to_date("2019-10-01")
    ticker = DummyTicker("AAA")

    setup_logging(logging.INFO, console_logging=True)

    OnNewBarEvent.set_frequency(Frequency.MIN_15)
    OnNewBarEvent.set_start_and_end_time({"hour": 10, "minute": 0, "second": 0, "microsecond": 0},
                                         {"hour": 13, "minute": 0, "second": 0, "microsecond": 0})

    # configuration
    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_frequency(Frequency.MIN_1)
    session_builder.set_backtest_name(backtest_name)
    session_builder.set_data_provider(intraday_data_provider)

    ts = session_builder.build(start_date, end_date)

    OnNewBarSignalGeneration(IntradayMAStrategy(ts, ticker))
    ts.start_trading()


if __name__ == "__main__":
    main()
