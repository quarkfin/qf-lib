import logging
from datetime import datetime
from typing import List, Tuple, Type

import matplotlib.pyplot as plt
from dic.container import Container

from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.execution_handler.simulated.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.monitoring.light_backtest_monitor import LightBacktestMonitor
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.portfolio_handler import PortfolioHandler
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.backtesting.trading_session.notifiers import Notifiers
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.contract_to_ticker_conversion.quandl_mapper import DummyQuandlContractTickerMapper
from qf_lib.common.tickers.tickers import QuandlTicker, Ticker, BloombergTicker
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.settings import Settings


class BacktestTradingSessionBuilder(object):

    def __init__(self, container: Container, trading_tickers: List[Ticker], data_tickers: List[Ticker],
                 start_date: datetime, end_date: datetime):
        self._logger = qf_logger.getChild(self.__class__.__name__)

        self._tickers = trading_tickers + data_tickers
        self._data_history_start = start_date - RelativeDelta(years=1)

        self._start_date = start_date
        self._end_date = end_date

        self._initial_cash = 1000000
        self._is_lightweight = True
        self.set_backtest_name("Backtest Results")
        self._contract_ticker_mapper_setup(trading_tickers)

        self._settings = container.resolve(Settings)  # type: Settings
        self._data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider
        self._pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter
        self._excel_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter

        self._timer = SettableTimer(start_date)
        self._notifiers = Notifiers(self._timer)
        self._data_handler = DataHandler(self._data_provider, self._timer)
        self._portfolio = Portfolio(self._data_handler, self.initial_cash, self._timer, self._contract_ticker_mapper)
        self._backtest_result = BacktestResult(self._portfolio, self.backtest_name, start_date, end_date)

        self._monitor = self._monitor_setup(self.is_lightweight, self._backtest_result, self._settings,
                                            self._pdf_exporter,
                                            self._excel_exporter)
        self._console_logging_setup(self.is_lightweight)

        self.set_commission_model(FixedCommissionModel(0.0))  # to be set
        self.set_slippage_model(PriceBasedSlippage(0.0))  # to be set
        self._execution_handler = SimulatedExecutionHandler(self._data_handler, self._timer, self._notifiers.scheduler,
                                                            self._monitor, self._commission_model,
                                                            self._contract_ticker_mapper, self._portfolio,
                                                            self._slippage_model)

        self._broker = BacktestBroker(self._portfolio, self._execution_handler)
        self._order_factory = OrderFactory(self._broker, self._data_handler, self._contract_ticker_mapper)

        self._portfolio_handler = PortfolioHandler(self._portfolio, self._monitor, self._notifiers.scheduler)

        self._position_sizer = SimplePositionSizer(self._broker, self._data_handler, self._order_factory,
                                                   self._contract_ticker_mapper)

        self._events_manager = self._create_event_manager(self._timer, self._notifiers)

        self._time_flow_controller = BacktestTimeFlowController(self._notifiers.scheduler, self._events_manager,
                                                                self._timer, self._notifiers.empty_queue_event_notifier,
                                                                end_date)

        self._logger.info(
            "\n".join([
                "Creating Backtest Trading Session.",
                "\tBacktest Name: {}".format(self.backtest_name),
                "\tData Provider: {}".format(self._data_provider.__class__.__name__),
                "\tContract - Ticker Mapper: {}".format(self._contract_ticker_mapper.__class__.__name__),
                "\tStart Date: {}".format(start_date),
                "\tEnd Date: {}".format(end_date),
                "\tInitial Cash: {:.2f}".format(self.initial_cash)
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

    def set_is_lightweight(self, is_lightweight: bool):
        self.is_lightweight = is_lightweight

    def set_initial_cash(self, initial_cash: int):
        assert type(initial_cash) is int and initial_cash > 0
        self.initial_cash = initial_cash

    def set_backtest_name(self, name: str):
        self.backtest_name = name

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

        self.backtest_name = name

    def _contract_ticker_mapper_setup(self, trading_tickers):
        assert trading_tickers
        trading_tickers = list(set(trading_tickers))
        ticker_type = type(trading_tickers[0])
        assert all(isinstance(ticker, ticker_type) for ticker in trading_tickers)

        if ticker_type is QuandlTicker:
            contract_ticker_mapper = DummyQuandlContractTickerMapper()
        elif ticker_type is BloombergTicker:
            contract_ticker_mapper = DummyBloombergContractTickerMapper()
        else:
            assert False, "ticker type cannot be handled"

        self._contract_ticker_mapper = contract_ticker_mapper  # type: ContractTickerMapper

    def _monitor_setup(self, is_lightweight, backtest_result, settings, pdf_exporter, excel_exporter):
        if is_lightweight:
            monitor_type = LightBacktestMonitor
        else:
            monitor_type = BacktestMonitor
        return monitor_type(backtest_result, settings, pdf_exporter, excel_exporter)

    def _console_logging_setup(self, is_lightweight):
        if is_lightweight:
            logging_level = logging.WARNING
        else:
            logging_level = logging.INFO
        setup_logging(level=logging_level, console_logging=True)

    def set_commission_model(self, commission_model: CommissionModel):
        self._commission_model = commission_model

    def set_slippage_model(self, slippage_model: Slippage):
        self._slippage_model = slippage_model

    def build(self):
        ts = BacktestTradingSession(
            contract_ticker_mapper=self._contract_ticker_mapper,
            start_date=self._start_date,
            end_date=self._end_date,
            position_sizer=self._position_sizer,
            data_handler=self._data_handler,
            timer=self._timer,
            notifiers=self._notifiers,
            portfolio=self._portfolio,
            events_manager=self._events_manager,
            monitor=self._monitor,
            broker=self._broker,
            order_factory=self._order_factory
        )
        ts.data_handler.use_data_bundle(self._tickers, PriceField.ohlcv(), self._data_history_start, ts.end_date)
        return ts

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
