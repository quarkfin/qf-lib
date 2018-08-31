from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import \
    DummyBloombergContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.backtesting.execution_handler.simulated.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.monitoring.dummy_monitor import DummyMonitor
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.portfolio_handler import PortfolioHandler
from qf_lib.backtesting.position_sizer.naive_position_sizer import NaivePositionSizer
from qf_lib.backtesting.risk_manager.naive_risk_manager import NaiveRiskManager
from qf_lib.backtesting.trading_session.notifiers import Notifiers
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider


class TestingTradingSession(object):
    """
    Encapsulates the settings and components for carrying out a backtest session. Pulls for data every day.
    """

    def __init__(self, data_provider: GeneralPriceProvider, start_date, end_date, initial_cash):
        """
        Set up the backtest variables according to what has been passed in.
        """
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.logger.info(
            "\n".join([
                "Testing the Backtester:",
                "Start date: {:s}".format(date_to_str(start_date)),
                "End date: {:s}".format(date_to_str(end_date)),
                "Initial cash: {:.2f}".format(initial_cash)
            ])
        )

        position_sizer = NaivePositionSizer()
        timer = SettableTimer(start_date)
        risk_manager = NaiveRiskManager(timer)
        notifiers = Notifiers(timer)
        data_handler = DataHandler(data_provider, timer)
        events_manager = self._create_event_manager(timer, notifiers)
        contract_to_tickers_mapper = DummyBloombergContractTickerMapper()

        portfolio = Portfolio(data_handler, initial_cash, timer, contract_to_tickers_mapper)

        backtest_result = BacktestResult(portfolio=portfolio, backtest_name="Testing the Backtester",
                                         start_date=start_date, end_date=end_date)

        monitor = DummyMonitor(backtest_result)
        commission_model = FixedCommissionModel(0.0)

        execution_handler = SimulatedExecutionHandler(
            events_manager, data_handler, timer, notifiers.scheduler, monitor, commission_model,
            contract_to_tickers_mapper, portfolio)

        broker = BacktestBroker(portfolio, execution_handler)
        order_factory = OrderFactory(broker, data_handler, contract_to_tickers_mapper)

        time_flow_controller = BacktestTimeFlowController(
            notifiers.scheduler, events_manager, timer, notifiers.empty_queue_event_notifier, end_date
        )
        portfolio_handler = PortfolioHandler(
            execution_handler, portfolio, position_sizer, risk_manager, monitor, notifiers.scheduler
        )

        self.logger.info(
            "\n".join([
                "Configuration of components:",
                "Position sizer: {:s}".format(position_sizer.__class__.__name__),
                "Timer: {:s}".format(timer.__class__.__name__),
                "Risk Manager: {:s}".format(risk_manager.__class__.__name__),
                "Data Provider: {:s}".format(data_provider.__class__.__name__),
                "Backtest Result: {:s}".format(backtest_result.__class__.__name__),
                "Monitor: {:s}".format(monitor.__class__.__name__),
                "Execution Handler: {:s}".format(execution_handler.__class__.__name__),
                "Commission Model: {:s}".format(commission_model.__class__.__name__),
                "Broker: {:s}".format(broker.__class__.__name__),
                "Contract-Ticker Mapper: {:s}".format(contract_to_tickers_mapper.__class__.__name__)
            ])
        )

        self.broker = broker
        self.notifiers = notifiers
        self.initial_cash = initial_cash
        self.start_date = start_date
        self.end_date = end_date
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
        self.monitor.end_of_trading_update(self.timer.now())
