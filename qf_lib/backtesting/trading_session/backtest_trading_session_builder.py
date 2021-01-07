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
import inspect
from datetime import datetime
from typing import List, Tuple, Type, Dict

from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.contract.contract_to_ticker_conversion.simulated_bloomberg_mapper import \
    SimulatedBloombergContractTickerMapper
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
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitorSettings, BacktestMonitor
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.monitoring.signals_register import SignalsRegister
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.orders_filter.orders_filter import OrdersFilter
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.config_exporter import ConfigExporter
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.settings import Settings


class BacktestTradingSessionBuilder(object):
    """
    Class used to build a Trading Session with all necessary elements, connections and dependencies.
    By default it uses the following settings:

    - backtest name is set to "Backtest Results"
    - initial cash is set to 10000000
    - montior type is set to LightBacktestMonitor
    - SimulatedBloombergContractTickerMapper is used to map contracts to tickers
    - no commissions are introduced (FixedCommissionModel(0.0))
    - no slippage is introduced (PriceBasedSlippage(0.0))
    - SimplePositionSizer is used
    - BeforeMarketOpenEvent is triggered at 08:00
    - MarketOpenEvent is triggered at 13:30
    - MarketCloseEvent is triggered at 20:00
    - AfterMarketCloseEvent is triggered at 23:00

    Parameters
    ------------
    data_provider: GeneralPriceProvider
        data provider used to download all fields and prices used during trading
    settings: Settings
        object containing all necessary settings, used for example for connection purposes
    pdf_exporter: PDFExporter
        used to export all trading statistics to PDF
    excel_exporter: ExcelExporter
        used to export trading data to Excel
    """

    def __init__(self, data_provider: GeneralPriceProvider, settings: Settings, pdf_exporter: PDFExporter,
                 excel_exporter: ExcelExporter):
        self._logger = qf_logger.getChild(self.__class__.__name__)

        self._backtest_name = "Backtest Results"
        self._initial_cash = 10000000
        self._benchmark_tms = None
        self._monitor_settings = None

        self._contract_ticker_mapper = SimulatedBloombergContractTickerMapper()

        self._commission_model_type = FixedCommissionModel
        self._commission_model_kwargs = {"commission": 0.0}

        self._slippage_model_type = PriceBasedSlippage
        self._slippage_model_kwargs = {"slippage_rate": 0.0, "max_volume_share_limit": None}

        self._position_sizer_type = SimplePositionSizer
        self._position_sizer_kwargs = dict()

        self._orders_filter_types_params = []  # type: List[Tuple[Type[OrdersFilter], Dict]]

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

    @ConfigExporter.update_config
    def set_backtest_name(self, name: str):
        """Sets backtest name.

        Parameters
        -----------
        name: str
            new backtest name
        """
        assert not any(char in name for char in '/\\?%*:|"<>')
        self._backtest_name = name

    @ConfigExporter.update_config
    def set_frequency(self, frequency: Frequency):
        """Sets the frequency of the backtest. Based on this either DailyDataHandler or
        IntradayDataHandler is chosen.

        Parameters
        -----------
        frequency: Frequency
            frequency of the data and prices
        """
        self._frequency = frequency

    @ConfigExporter.update_config
    def set_scheduling_time_delay(self, time_delay: RelativeDelta):
        """Sets the scheduling delay.

        Parameters
        -----------
        time_delay: RelativeDelta
            scheduling time delay
        """
        self._scheduling_time_delay = time_delay

    @ConfigExporter.update_config
    def set_initial_cash(self, initial_cash: int):
        """Sets the initial cash value.

        Parameters
        -----------
        initial_cash: int
        """
        assert type(initial_cash) is int and initial_cash > 0
        self._initial_cash = initial_cash

    @ConfigExporter.update_config
    def set_data_provider(self, data_provider: DataProvider):
        """Sets the data provider.

        Parameters
        -----------
        data_provider: DataProvider
            data provider used to download data and prices
        """
        self._data_provider = data_provider

    @ConfigExporter.update_config
    def set_monitor_settings(self, monitor_settings: BacktestMonitorSettings):
        """Sets type of the monitor.

        Parameters
        -----------
        monitor_settings:
            object defining the outputs that we want the BacktestMonitor to generate
        """
        if not type(monitor_settings) is BacktestMonitorSettings:
            self._logger.error("Monitor settings of different type "
                               "than BacktestMonitorSettings: {}".format(monitor_settings))
        else:
            self._monitor_settings = monitor_settings

    def set_benchmark_tms(self, benchmark_tms: QFSeries):
        """Sets the benchmark timeseries. If set, the TearsheetWithBenchamrk will be generated.

        Parameters
        -----------
        benchmark_tms: QFSeries
            timeseries of the benchmark
        """
        self._benchmark_tms = benchmark_tms

    @ConfigExporter.update_config
    def set_contract_ticker_mapper(self, contract_ticker_mapper: ContractTickerMapper):
        """Sets the mapping between contracts and tickers.

        Parameters
        -----------
        contract_ticker_mapper: ContractTickerMapper
            mapping between contracts and tickers
        """
        self._contract_ticker_mapper = contract_ticker_mapper

    @ConfigExporter.update_config
    def set_commission_model(self, commission_model_type: Type[CommissionModel], **kwargs):
        """Sets commission model.

        Parameters
        -----------
        commission_model_type: Type[CommissionModel]
            type of the commission model
        kwargs:
            all keyword parameters necessary to initialize the chosen commission model
        """
        try:
            # Verify if all required parameters were passed to the function. All the parameters that are necessary for
            # the CommissionModel constructor will be passed along with the kwargs
            commission_model_params = dict(inspect.signature(CommissionModel).parameters)
            commission_model_params.update(kwargs)
            inspect.signature(commission_model_type).bind(**commission_model_params)

            self._commission_model_type = commission_model_type
            self._commission_model_kwargs = kwargs
        except TypeError as e:
            self._logger.error("The Commission Model could not be set correctly - {}".format(e))

    @ConfigExporter.update_config
    def set_slippage_model(self, slippage_model_type: Type[Slippage], **kwargs):
        """Sets the slippage model. The parameters to initialize the Slippage should be passed as keyword arguments.
        Parameters corresponding to data provider and contract ticker mapper should not be provided, as they are
        setup by the backtest trading session builder. For example to set slippage model to price based slippage with
        slippage_rate = 0.1 the following command should be called on the session builder:
        builder.set_slippage_model(PriceBasedSlippage, slippage_rate=0.1)

        Parameters
        -----------
        slippage_model_type: Type[Slippage]
            type of the slippage model
        kwargs:
            all keyword parameters which are necessary to initialize the chosen slippage model
        """
        try:
            # Verify if all required parameters were passed to the function. All the parameters that are necessary for
            # the Slippage constructor will be passed along with the kwargs
            slippage_model_params = dict(inspect.signature(Slippage).parameters)
            slippage_model_params.update(kwargs)
            inspect.signature(slippage_model_type).bind(**slippage_model_params)

            self._slippage_model_type = slippage_model_type
            self._slippage_model_kwargs = kwargs
        except TypeError as e:
            self._logger.error("The Slippage Model could not be set correctly - {}".format(e))

    @ConfigExporter.update_config
    def set_position_sizer(self, position_sizer_type: Type[PositionSizer], **kwargs):
        """Sets the position sizer. The parameters to initialize the PositionSizer should be passed as keyword
        arguments. Parameters corresponding to the broker, data handler, contract ticker mapper or signals register
        should not be provided, as all these parameters are setup by the backtest trading session builder.
        For example to set position sizer with initial risk = 0.3 and tolerance percentage = 0.1 the following command
        should be called on the session builder:

        builder.set_position_sizer(InitialRiskWithVolumePositionSizer, initial_risk=0.3, tolerance_percentage=0.1)

        Parameters
        -----------
        position_sizer_type: Type[PositionSizer]
            type of position sizer
        kwargs:
            all keyword parameters which are necessary to initialize the chosen position sizer
        """
        try:
            # Verify if all required parameters were passed to the function. All the parameters that are necessary for
            # the PositionSizer constructor will be passed along with the kwargs
            position_sizer_params = dict(inspect.signature(PositionSizer).parameters)
            position_sizer_params.update(kwargs)
            inspect.signature(position_sizer_type).bind(**position_sizer_params)

            self._position_sizer_type = position_sizer_type
            self._position_sizer_kwargs = kwargs
        except TypeError as e:
            self._logger.error("The Position Sizer could not be set correctly - {}".format(e))

    @ConfigExporter.append_config
    def add_orders_filter(self, orders_filter_type: Type[OrdersFilter], **kwargs):
        """Adds orders filter to the pipeline. Ths parameters to initialize the OrdersFilter should be passed as keyword
        arguments. Parameters corresponding to data handler and contract ticker mapper should not be provided, as
        they are setup by the backtest trading session builder. For example to set orders filter with
        volume_percentage_limit = 0.3 the following command should be called on the session builder:

        builder.add_orders_filter(VolumeOrdersFilter, volume_percentage_limit=0.3)

        Parameters
        -----------
        orders_filter_type: Type[OrdersFilter]
            type of position sizer
        kwargs:
            all keyword parameters which are necessary to initialize the chosen orders filter
        """
        try:
            # Verify if all required parameters were passed to the function. All the parameters that are necessary for
            # the OrdersFilter constructor will be passed along with the kwargs
            orders_filter_params = dict(inspect.signature(OrdersFilter).parameters)
            orders_filter_params.update(kwargs)
            inspect.signature(orders_filter_type).bind(**orders_filter_params)
            self._orders_filter_types_params.append((orders_filter_type, kwargs))
        except TypeError as e:
            self._logger.error("The Orders Filter could not be added to the pipeline - {}".format(e))

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
                             "Frequency.DAILY and Frequency.MIN_1. "
                             "\nMake sure you set the frequency in the session builder for example: "
                             "\n\t-> 'session_builder.set_frequency(Frequency.DAILY)'")

        return data_handler

    def build(self, start_date: datetime, end_date: datetime) -> BacktestTradingSession:
        """Builds a backtest trading session.

        Parameters
        -----------
        start_date: datetime
            starting date of the backtest
        end_date: datetime
            last date of the backtest

        Returns
        ---------
        BacktestTradingSession
            trading session containing all the necessary parameters
        """
        self._timer = SettableTimer(start_date)
        self._notifiers = Notifiers(self._timer)
        self._events_manager = self._create_event_manager(self._timer, self._notifiers)

        self._data_handler = self._create_data_handler(self._data_provider, self._timer)
        signals_register = SignalsRegister()

        self._portfolio = Portfolio(self._data_handler, self._initial_cash, self._timer, self._contract_ticker_mapper)
        self._backtest_result = BacktestResult(self._portfolio, signals_register, self._backtest_name, start_date,
                                               end_date)
        self._monitor = self._monitor_setup()

        self._slippage_model = self._slippage_model_setup()
        self._commission_model = self._commission_model_setup()
        self._execution_handler = SimulatedExecutionHandler(
            self._data_handler, self._timer, self._notifiers.scheduler, self._monitor, self._commission_model,
            self._contract_ticker_mapper, self._portfolio, self._slippage_model,
            scheduling_time_delay=self._scheduling_time_delay, frequency=self._frequency)

        self._time_flow_controller = BacktestTimeFlowController(
            self._notifiers.scheduler, self._events_manager, self._timer,
            self._notifiers.empty_queue_event_notifier, end_date)

        self._broker = BacktestBroker(self._portfolio, self._execution_handler)
        self._order_factory = OrderFactory(self._broker, self._data_handler, self._contract_ticker_mapper)
        self._position_sizer = self._position_sizer_setup(signals_register)
        self._orders_filters = self._orders_filter_setup()

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
            orders_filters=self._orders_filters,
            data_handler=self._data_handler,
            timer=self._timer,
            notifiers=self._notifiers,
            portfolio=self._portfolio,
            events_manager=self._events_manager,
            monitor=self._monitor,
            broker=self._broker,
            order_factory=self._order_factory,
            frequency=self._frequency,
            backtest_result=self._backtest_result
        )

        return ts

    def _monitor_setup(self) -> BacktestMonitor:
        monitor = BacktestMonitor(self._backtest_result, self._settings, self._pdf_exporter,
                                  self._excel_exporter, self._monitor_settings, self._benchmark_tms)
        return monitor

    def _position_sizer_setup(self, signals_register: SignalsRegister):
        return self._position_sizer_type(
            self._broker, self._data_handler, self._order_factory, self._contract_ticker_mapper, signals_register,
            **self._position_sizer_kwargs)

    def _orders_filter_setup(self):
        orders_filters = []
        for orders_filter_type, kwargs in self._orders_filter_types_params:
            orders_filter = orders_filter_type(self._data_handler, self._contract_ticker_mapper, **kwargs)
            orders_filters.append(orders_filter)
        return orders_filters

    def _slippage_model_setup(self):
        return self._slippage_model_type(data_provider=self._data_provider,
                                         contract_ticker_mapper=self._contract_ticker_mapper,
                                         **self._slippage_model_kwargs)

    def _commission_model_setup(self):
        return self._commission_model_type(**self._commission_model_kwargs)
