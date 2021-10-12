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
from qf_lib.backtesting.strategies.abstract_strategy import AbstractStrategy
from qf_lib.backtesting.strategies.signal_generators import OnBeforeMarketOpenSignalGeneration
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from demo_scripts.demo_configuration.demo_ioc import container
import matplotlib.pyplot as plt

from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.frequency import Frequency

plt.ion()  # required for dynamic chart, keep before other imports


class BuyAndHoldStrategy(AbstractStrategy):
    """
    A testing strategy that simply purchases (longs) an asset as soon as it starts and then holds until the completion
    of a backtest.
    """

    CONTRACT = Contract(symbol="SPY US Equity", security_type='STK', exchange='NASDAQ')
    TICKER = BloombergTicker("SPY US Equity")

    def __init__(self, ts: TradingSession):
        super().__init__(ts)
        self.order_factory = ts.order_factory
        self.broker = ts.broker

        self.invested = False

    def calculate_and_place_orders(self):
        if not self.invested:
            orders = self.order_factory.percent_orders({self.CONTRACT: 1.0}, MarketOrder(), TimeInForce.GTC)

            self.broker.place_orders(orders)
            self.invested = True


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2018-01-01")

    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_backtest_name('Buy and Hold')
    session_builder.set_frequency(Frequency.DAILY)
    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(BuyAndHoldStrategy.TICKER)

    OnBeforeMarketOpenSignalGeneration(BuyAndHoldStrategy(ts))
    ts.start_trading()


if __name__ == "__main__":
    main()
