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
from qf_lib.common.utils.dateutils.timer import SettableTimer, Timer
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
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.tickers = trading_tickers + data_tickers
        self.data_history_start = start_date - RelativeDelta(years=1)

        self.start_date = start_date
        self.end_date = end_date

        self.set_initial_cash(1000000)
        self.set_is_lightweight(True)
        self.set_backtest_name("backtest")
        self.set_contract_ticker_mapper(trading_tickers)

        self.set_settings(container.resolve(Settings))
        self.set_data_provider(container.resolve(GeneralPriceProvider))
        self.set_pdf_exporter(container.resolve(PDFExporter))
        self.set_excel_exporter(container.resolve(ExcelExporter))

        self.set_settable_timer(start_date)
        self.set_notifiers(self.timer)
        self.set_data_handler(self.data_provider, self.timer)
        self.portfolio = Portfolio(self.data_handler, self.initial_cash, self.timer, self.contract_ticker_mapper)
        self.backtest_result = BacktestResult(self.portfolio, self.backtest_name, start_date, end_date)

        self.set_monitor(self.is_lightweight, self.backtest_result, self.settings, self.pdf_exporter,
                         self.excel_exporter)

        self.set_commission_model(FixedCommissionModel(0.0))
        self.set_slippage_model(PriceBasedSlippage(0.0))
        self.execution_handler = SimulatedExecutionHandler(self.data_handler, self.timer, self.notifiers.scheduler,
                                                           self.monitor, self.commission_model,
                                                           self.contract_ticker_mapper, self.portfolio,
                                                           self.slippage_model)

        self.broker = BacktestBroker(self.portfolio, self.execution_handler)
        self.order_factory = OrderFactory(self.broker, self.data_handler, self.contract_ticker_mapper)

        self.portfolio_handler = PortfolioHandler(self.portfolio, self.monitor, self.notifiers.scheduler)

        self.position_sizer = SimplePositionSizer(self.broker, self.data_handler, self.order_factory,
                                                  self.contract_ticker_mapper)

        self.events_manager = self._create_event_manager(self.timer, self.notifiers)  # to build

        self.time_flow_controller = BacktestTimeFlowController(self.notifiers.scheduler, self.events_manager,
                                                               self.timer, self.notifiers.empty_queue_event_notifier,
                                                               end_date)

        self.logger.info(
            "\n".join([
                "Creating Backtest Trading Session.",
                "\tBacktest Name: {}".format(self.backtest_name),
                "\tData Provider: {}".format(self.data_provider.__class__.__name__),
                "\tContract - Ticker Mapper: {}".format(self.contract_ticker_mapper.__class__.__name__),
                "\tStart Date: {}".format(start_date),
                "\tEnd Date: {}".format(end_date),
                "\tInitial Cash: {:.2f}".format(self.initial_cash)
            ])
        )

        self.logger.info(
            "\n".join([
                "Configuration of components:",
                "\tPosition sizer: {:s}".format(self.position_sizer.__class__.__name__),
                "\tTimer: {:s}".format(self.timer.__class__.__name__),
                "\tData Handler: {:s}".format(self.data_handler.__class__.__name__),
                "\tBacktest Result: {:s}".format(self.backtest_result.__class__.__name__),
                "\tMonitor: {:s}".format(self.monitor.__class__.__name__),
                "\tExecution Handler: {:s}".format(self.execution_handler.__class__.__name__),
                "\tSlippage Model: {:s}".format(self.slippage_model.__class__.__name__),
                "\tCommission Model: {:s}".format(self.commission_model.__class__.__name__),
                "\tBroker: {:s}".format(self.broker.__class__.__name__),
            ])
        )

    def set_is_lightweight(self, is_lightweight: bool):
        self.is_lightweight = is_lightweight
        self.set_console_logging(self.is_lightweight)

    def set_console_logging(self, is_lightweight):
        if is_lightweight:
            logging_level = logging.WARNING
        else:
            logging_level = logging.INFO
        setup_logging(level=logging_level, console_logging=True)

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

    def set_contract_ticker_mapper(self, trading_tickers):
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

        self.contract_ticker_mapper = contract_ticker_mapper  # type: ContractTickerMapper

    def set_settable_timer(self, start_date):
        self.timer = SettableTimer(start_date)

    def set_notifiers(self, timer):
        self.notifiers = Notifiers(timer)

    def set_data_handler(self, data_provider: GeneralPriceProvider, timer: Timer):
        self.data_handler = DataHandler(data_provider, timer)

    def set_monitor(self, is_lightweight, backtest_result, settings, pdf_exporter, excel_exporter):
        if is_lightweight:
            monitor_type = LightBacktestMonitor
        else:
            monitor_type = BacktestMonitor
        self.monitor = monitor_type(backtest_result, settings, pdf_exporter, excel_exporter)

    def set_settings(self, settings: Settings):
        self.settings = settings

    def set_data_provider(self, data_provider: GeneralPriceProvider):
        self.data_provider = data_provider

    def set_pdf_exporter(self, pdf_exporter: PDFExporter):
        self.pdf_exporter = pdf_exporter

    def set_excel_exporter(self, excel_exporter: ExcelExporter):
        self.excel_exporter = excel_exporter

    def set_commission_model(self, commission_model: CommissionModel):
        self.commission_model = commission_model

    def set_slippage_model(self, slippage_model: Slippage):
        self.slippage_model = slippage_model

    def build(self):
        ts = BacktestTradingSession(
            contract_ticker_mapper=self.contract_ticker_mapper,
            start_date=self.start_date,
            end_date=self.end_date,
            position_sizer=self.position_sizer,
            data_handler=self.data_handler,
            timer=self.timer,
            notifiers=self.notifiers,
            portfolio=self.portfolio,
            events_manager=self.events_manager,
            monitor=self.monitor,
            broker=self.broker,
            order_factory=self.order_factory
        )
        ts.data_handler.use_data_bundle(self.tickers, PriceField.ohlcv(), self.data_history_start, ts.end_date)
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
