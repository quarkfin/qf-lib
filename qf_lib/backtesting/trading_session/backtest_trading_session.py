from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.monitoring.light_backtest_monitor import LightBacktestMonitor
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.portfolio_handler import PortfolioHandler
from qf_lib.backtesting.position_sizer.naive_position_sizer import NaivePositionSizer
from qf_lib.backtesting.risk_manager.naive_risk_manager import NaiveRiskManager
from qf_lib.backtesting.trading_session.notifiers import Notifiers
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.price_data_provider import DataProvider
from qf_lib.settings import Settings


class BacktestTradingSession(object):
    """
    Encapsulates the settings and components for carrying out a backtest session. Pulls for data every day.
    """

    def __init__(self, backtest_name: str, settings: Settings, data_provider: DataProvider,
                 contract_ticker_mapper: ContractTickerMapper, pdf_exporter: PDFExporter,
                 excel_exporter: ExcelExporter, start_date, end_date, initial_cash, is_lightweight: False):
        """
        Set up the backtest variables according to what has been passed in.
        """
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.backtest_name = backtest_name
        self.contract_ticker_mapper = contract_ticker_mapper
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash

        self.logger.info(
            "\n".join([
                "Creating Backtest Trading Session.",
                "\tBacktest Name: {}".format(backtest_name),
                "\tData Provider: {}".format(data_provider.__class__.__name__),
                "\tContract - Ticker Mapper: {}".format(contract_ticker_mapper.__class__.__name__),
                "\tStart Date: {}".format(date_to_str(start_date)),
                "\tEnd Date: {}".format(date_to_str(end_date)),
                "\tInitial Cash: {:.2f}".format(initial_cash)
            ])
        )

        position_sizer = NaivePositionSizer()
        timer = SettableTimer(start_date)
        risk_manager = NaiveRiskManager(timer)
        notifiers = Notifiers(timer)
        data_handler = DataHandler(data_provider, timer)
        events_manager = self._create_event_manager(timer, notifiers)

        portfolio = Portfolio(data_handler, initial_cash, timer, contract_ticker_mapper)

        backtest_result = BacktestResult(portfolio=portfolio, backtest_name=backtest_name,
                                         start_date=start_date, end_date=end_date)

        if is_lightweight:
            monitor = LightBacktestMonitor(backtest_result, settings, pdf_exporter, excel_exporter)
        else:
            monitor = BacktestMonitor(backtest_result, settings, pdf_exporter, excel_exporter)

        commission_model = FixedCommissionModel(0.0)

        execution_handler = SimulatedExecutionHandler(
            events_manager, data_handler, timer, notifiers.scheduler, monitor, commission_model,
            contract_ticker_mapper, portfolio)

        broker = BacktestBroker(portfolio, execution_handler)
        order_factory = OrderFactory(broker, data_handler, contract_ticker_mapper)

        time_flow_controller = BacktestTimeFlowController(
            notifiers.scheduler, events_manager, timer, notifiers.empty_queue_event_notifier, end_date
        )
        portfolio_handler = PortfolioHandler(
            execution_handler, portfolio, position_sizer, risk_manager, monitor, notifiers.scheduler
        )

        self.logger.info(
            "\n".join([
                "Configuration of components:",
                "\tPosition sizer: {:s}".format(position_sizer.__class__.__name__),
                "\tTimer: {:s}".format(timer.__class__.__name__),
                "\tRisk Manager: {:s}".format(risk_manager.__class__.__name__),
                "\tData Handler: {:s}".format(data_handler.__class__.__name__),
                "\tBacktest Result: {:s}".format(backtest_result.__class__.__name__),
                "\tMonitor: {:s}".format(monitor.__class__.__name__),
                "\tExecution Handler: {:s}".format(execution_handler.__class__.__name__),
                "\tCommission Model: {:s}".format(commission_model.__class__.__name__),
                "\tBroker: {:s}".format(broker.__class__.__name__),
            ])
        )

        self.notifiers = notifiers

        self.event_manager = events_manager
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.portfolio_handler = portfolio_handler
        self.execution_handler = execution_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.monitor = monitor
        self.timer = timer
        self.order_factory = order_factory
        self.time_flow_controller = time_flow_controller
        self.broker = broker


    @staticmethod
    def _create_event_manager(timer, notifiers: Notifiers):
        events_manager = EventManager(timer)

        events_manager.register_notifiers([
            notifiers.all_event_notifier,
            notifiers.empty_queue_event_notifier,
            notifiers.end_trading_event_notifier,
            notifiers.scheduler
        ])
        return events_manager

    def start_trading(self) -> None:
        """
        Carries out an while loop that processes incoming events. The loop continues until the EndTradingEvent occurs
        (e.g. no more data for the backtest).
        """
        self.logger.info("Running backtest...")
        while self.event_manager.continue_trading:
            self.event_manager.dispatch_next_event()

        self.logger.info("Backtest finished, generating report...")
        self.monitor.end_of_trading_update()
