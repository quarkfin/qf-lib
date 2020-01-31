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
from typing import List, Tuple, Type

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.contract.contract_to_ticker_conversion.bloomberg_mapper import \
    DummyBloombergContractTickerMapper
from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.data_handler.intraday_data_handler import IntradayDataHandler
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.events.time_event.regular_time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.monitoring.dummy_monitor import DummyMonitor
from qf_lib.backtesting.monitoring.light_backtest_monitor import LightBacktestMonitor
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import QuandlTicker, Ticker, BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.settings import Settings


class BacktestTradingSessionBuilder(object):

    def __init__(self, data_provider: GeneralPriceProvider, settings: Settings, pdf_exporter: PDFExporter,
                 excel_exporter: ExcelExporter):
        self._logger = qf_logger.getChild(self.__class__.__name__)

        self._backtest_name = "Backtest Results"
        self._initial_cash = 10000000
        self._monitor_type = LightBacktestMonitor
        self._benchmark_tms = None

        self._contract_ticker_mapper = DummyBloombergContractTickerMapper()
        self._commission_model = FixedCommissionModel(0.0)
        self._slippage_model = PriceBasedSlippage(0.0)
        self._position_sizer_type = SimplePositionSizer
        self._position_sizer_param = None

        self._data_provider = data_provider
        self._settings = settings
        self._pdf_exporter = pdf_exporter
        self._excel_exporter = excel_exporter

        self._frequency = None
        self._scheduling_time_delay = RelativeDelta(minutes=1)

        BeforeMarketOpenEvent.set_trigger_time({"hour": 8, "minute": 0, "second": 0, "microsecond": 0})
        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})
        AfterMarketCloseEvent.set_trigger_time({"hour": 23, "minute": 00, "second": 0, "microsecond": 0})

    def set_backtest_name(self, name: str):
        assert not any(char in name for char in ('/\\?%*:|"<>'))
        self._backtest_name = name

    def set_frequency(self, frequency: Frequency):
        self._frequency = frequency

    def set_scheduling_time_delay(self, time_delay: RelativeDelta):
        self._scheduling_time_delay = time_delay

    def set_initial_cash(self, initial_cash: int):
        assert type(initial_cash) is int and initial_cash > 0
        self._initial_cash = initial_cash

    def set_alpha_model_backtest_name(self, model_type: Type[AlphaModel], param_set: Tuple, tickers: List[Ticker]):
        name = model_type.__name__ + '_' + '_'.join((str(item)) for item in param_set)

        if len(tickers) <= 3:
            for ticker in tickers:
                ticker_str = ticker.as_string()

                if isinstance(ticker, QuandlTicker):
                    ticker_str = ticker_str.rsplit("/", 1)[-1]
                elif isinstance(ticker, BloombergTicker):
                    ticker_str = ticker_str.split(" ", 1)[0]

                name = name + '_' + ticker_str

        self._backtest_name = name

    def set_data_provider(self, data_provider: DataProvider):
        self._data_provider = data_provider

    def set_monitor_type(self, monitor_type: Type[AbstractMonitor]):
        assert issubclass(monitor_type, AbstractMonitor)
        self._monitor_type = monitor_type

    def set_benchmark_tms(self, benchmark_tms: QFSeries):
        self._benchmark_tms = benchmark_tms

    def set_contract_ticker_mapper(self, contract_ticker_mapper: ContractTickerMapper):
        self._contract_ticker_mapper = contract_ticker_mapper

    def set_commission_model(self, commission_model: CommissionModel):
        self._commission_model = commission_model

    def set_slippage_model(self, slippage_model: Slippage):
        self._slippage_model = slippage_model

    def set_position_sizer(self, position_sizer_type: Type[PositionSizer], param: float = None):
        if position_sizer_type is SimplePositionSizer:
            assert param is None
        if position_sizer_type is InitialRiskPositionSizer:
            assert param is not None
        self._position_sizer_type = position_sizer_type
        self._position_sizer_param = param

    @staticmethod
    def _create_event_manager(timer, notifiers: Notifiers):
        event_manager = EventManager(timer)

        event_manager.register_notifiers([
            notifiers.all_event_notifier,
            notifiers.empty_queue_event_notifier,
            notifiers.end_trading_event_notifier,
            notifiers.scheduler
        ])
        return event_manager

    def _create_data_handler(self, data_provider, timer):
        if self._frequency == Frequency.MIN_1:
            data_handler = IntradayDataHandler(data_provider, timer)
        elif self._frequency == Frequency.DAILY:
            data_handler = DailyDataHandler(data_provider, timer)
        else:
            raise ValueError("Invalid frequency parameter. The only frequencies supported by the DataHandler are "
                             "Frequency.DAILY and Frequency.MIN_1.")

        return data_handler

    def build(self, start_date: datetime, end_date: datetime) -> BacktestTradingSession:
        self._timer = SettableTimer(start_date)
        self._notifiers = Notifiers(self._timer)
        self._events_manager = self._create_event_manager(self._timer, self._notifiers)

        self._data_handler = self._create_data_handler(self._data_provider, self._timer)

        self._portfolio = Portfolio(self._data_handler, self._initial_cash, self._timer, self._contract_ticker_mapper)
        self._backtest_result = BacktestResult(self._portfolio, self._backtest_name, start_date, end_date)
        self._monitor = self._monitor_setup()

        self._execution_handler = SimulatedExecutionHandler(
            self._data_handler, self._timer, self._notifiers.scheduler, self._monitor, self._commission_model,
            self._contract_ticker_mapper, self._portfolio, self._slippage_model,
            scheduling_time_delay=self._scheduling_time_delay, frequency=self._frequency)

        self._time_flow_controller = BacktestTimeFlowController(
            self._notifiers.scheduler, self._events_manager, self._timer,
            self._notifiers.empty_queue_event_notifier, end_date)

        self._broker = BacktestBroker(self._portfolio, self._execution_handler)
        self._order_factory = OrderFactory(self._broker, self._data_handler, self._contract_ticker_mapper)
        self._position_sizer = self._position_sizer_setup()

        self._logger.info(
            "\n".join([
                "Creating Backtest Trading Session.",
                "\tBacktest Name: {}".format(self._backtest_name),
                "\tData Provider: {}".format(self._data_provider.__class__.__name__),
                "\tContract - Ticker Mapper: {}".format(self._contract_ticker_mapper.__class__.__name__),
                "\tStart Date: {}".format(start_date),
                "\tEnd Date: {}".format(end_date),
                "\tInitial Cash: {:.2f}".format(self._initial_cash)
            ])
        )

        self._logger.info(
            "\n".join([
                "Configuration of components:",
                "\tPosition sizer: {:s}".format(self._position_sizer.__class__.__name__),
                "\tTimer: {:s}".format(self._timer.__class__.__name__),
                "\tData Handler: {:s}".format(self._data_handler.__class__.__name__),
                "\tBacktest Result: {:s}".format(self._backtest_result.__class__.__name__),
                "\tMonitor: {:s}".format(self._monitor.__class__.__name__),
                "\tExecution Handler: {:s}".format(self._execution_handler.__class__.__name__),
                "\tSlippage Model: {:s}".format(self._slippage_model.__class__.__name__),
                "\tCommission Model: {:s}".format(self._commission_model.__class__.__name__),
                "\tBroker: {:s}".format(self._broker.__class__.__name__),
            ])
        )

        ts = BacktestTradingSession(
            contract_ticker_mapper=self._contract_ticker_mapper,
            start_date=start_date,
            end_date=end_date,
            position_sizer=self._position_sizer,
            data_handler=self._data_handler,
            timer=self._timer,
            notifiers=self._notifiers,
            portfolio=self._portfolio,
            events_manager=self._events_manager,
            monitor=self._monitor,
            broker=self._broker,
            order_factory=self._order_factory,
            frequency=self._frequency
        )
        return ts

    def _monitor_setup(self):
        if self._monitor_type is DummyMonitor:
            return DummyMonitor()
        monitor = self._monitor_type(self._backtest_result, self._settings, self._pdf_exporter, self._excel_exporter)
        if self._benchmark_tms is not None:
            monitor.set_benchmark(self._benchmark_tms)
        return monitor

    def _position_sizer_setup(self):
        if self._position_sizer_param is None:
            return self._position_sizer_type(
                self._broker, self._data_handler, self._order_factory, self._contract_ticker_mapper)
        else:
            return self._position_sizer_type(
                self._broker, self._data_handler, self._order_factory, self._contract_ticker_mapper,
                self._position_sizer_param)



