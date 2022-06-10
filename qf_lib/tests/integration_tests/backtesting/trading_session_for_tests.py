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
from unittest.mock import Mock

from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.simulated_contract_ticker_mapper import \
    SimulatedContractTickerMapper
from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.data_handler.intraday_data_handler import IntradayDataHandler
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.backtesting.signals.backtest_signals_register import BacktestSignalsRegister
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.data_provider import DataProvider


class TradingSessionForTests(TradingSession):
    """
    Encapsulates the settings and components for carrying out a backtest session. Pulls for data every day.
    """

    # initialise market time
    MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
    MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    def __init__(self, data_provider: DataProvider, start_date, end_date, initial_cash,
                 frequency: Frequency = Frequency.MIN_1):
        """
        Set up the backtest variables according to what has been passed in.
        """
        super().__init__()
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.logger.info(
            "\n".join([
                "Testing the Backtester:",
                "Start date: {:s}".format(date_to_str(start_date)),
                "End date: {:s}".format(date_to_str(end_date)),
                "Initial cash: {:.2f}".format(initial_cash),
                "Frequency of the simulated execution handler: {}".format(frequency)
            ])
        )

        timer = SettableTimer(start_date)
        notifiers = Notifiers(timer)
        if frequency <= Frequency.DAILY:
            data_handler = DailyDataHandler(data_provider, timer)
        else:
            data_handler = IntradayDataHandler(data_provider, timer)

        portfolio = Portfolio(data_handler, initial_cash, timer)
        signals_register = BacktestSignalsRegister()
        backtest_result = BacktestResult(portfolio=portfolio, backtest_name="Testing the Backtester",
                                         start_date=start_date, end_date=end_date, signals_register=signals_register)

        monitor = Mock(spec=BacktestMonitor)
        commission_model = FixedCommissionModel(0.0)
        slippage_model = PriceBasedSlippage(0.0, data_provider)

        execution_handler = SimulatedExecutionHandler(
            data_handler, timer, notifiers.scheduler, monitor, commission_model,
            portfolio, slippage_model, frequency=frequency)

        contract_ticker_mapper = SimulatedContractTickerMapper()
        broker = BacktestBroker(contract_ticker_mapper, portfolio, execution_handler)
        order_factory = OrderFactory(broker, data_handler)

        event_manager = self._create_event_manager(timer, notifiers)
        time_flow_controller = BacktestTimeFlowController(
            notifiers.scheduler, event_manager, timer, notifiers.empty_queue_event_notifier, end_date
        )
        position_sizer = SimplePositionSizer(broker, data_handler, order_factory, signals_register)

        self.logger.info(
            "\n".join([
                "Configuration of components:",
                "Position sizer: {:s}".format(position_sizer.__class__.__name__),
                "Timer: {:s}".format(timer.__class__.__name__),
                "Data Provider: {:s}".format(data_provider.__class__.__name__),
                "Backtest Result: {:s}".format(backtest_result.__class__.__name__),
                "Monitor: {:s}".format(monitor.__class__.__name__),
                "Execution Handler: {:s}".format(execution_handler.__class__.__name__),
                "Commission Model: {:s}".format(commission_model.__class__.__name__),
                "Broker: {:s}".format(broker.__class__.__name__),
            ])
        )

        self.broker = broker
        self.notifiers = notifiers
        self.initial_cash = initial_cash
        self.start_date = start_date
        self.end_date = end_date
        self.event_manager = event_manager
        self.contract_ticker_mapper = contract_ticker_mapper
        self.data_handler = data_handler
        self.data_provider = data_handler
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.position_sizer = position_sizer
        self.orders_filters = []
        self.monitor = monitor
        self.timer = timer
        self.order_factory = order_factory
        self.time_flow_controller = time_flow_controller
        self.frequency = frequency
