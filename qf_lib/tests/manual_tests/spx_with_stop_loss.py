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
from typing import Tuple

import matplotlib.pyplot as plt

from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
    CalculateAndPlaceOrdersRegularEvent
from qf_lib.backtesting.execution_handler.commission_models.ib_commission_model import IBCommissionModel
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitorSettings
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.strategies.abstract_strategy import AbstractStrategy
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports


class SpxWithStopLoss(AbstractStrategy):
    ticker = BloombergTicker("SPX Index")
    percentage = 0.005

    def __init__(self, ts: BacktestTradingSession):
        super().__init__(ts)
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.position_sizer = ts.position_sizer
        self.timer = ts.timer

    def calculate_and_place_orders(self):
        self.calculate_signals()

    def calculate_signals(self):
        last_price = self.data_handler.get_last_available_price(self.ticker, Frequency.DAILY)

        orders = self.order_factory.target_percent_orders({self.ticker: 1.0}, MarketOrder(),
                                                          time_in_force=TimeInForce.OPG, tolerance_percentage=0.02)

        stop_price = last_price * (1 - self.percentage)
        execution_style = StopOrder(stop_price=stop_price)
        stop_order = self.order_factory.percent_orders({self.ticker: -1}, execution_style=execution_style,
                                                       time_in_force=TimeInForce.DAY)

        self.broker.cancel_all_open_orders()
        self.broker.place_orders(orders)
        self.broker.place_orders(stop_order)


def run_strategy(data_provider: DataProvider) -> Tuple[float, str]:
    """ Returns the strategy end result and checksum of the preloaded data. """

    start_date = str_to_date("2017-01-01")
    end_date = str_to_date("2018-01-01")

    settings = get_test_settings()
    session_builder = BacktestTradingSessionBuilder(settings, PDFExporter(settings),
                                                    ExcelExporter(settings))
    session_builder.set_backtest_name('SPY w. stop ' + str(SpxWithStopLoss.percentage))
    session_builder.set_initial_cash(1000000)
    session_builder.set_frequency(Frequency.DAILY)
    session_builder.set_commission_model(IBCommissionModel)
    session_builder.set_data_provider(data_provider)
    session_builder.set_monitor_settings(BacktestMonitorSettings.no_stats())

    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(SpxWithStopLoss.ticker, RelativeDelta(days=40))

    strategy = SpxWithStopLoss(ts)
    CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
    CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
    strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

    ts.start_trading()

    data_checksum = ts.get_preloaded_data_checksum()
    actual_end_value = ts.portfolio.portfolio_eod_series()[-1]
    return actual_end_value, data_checksum
