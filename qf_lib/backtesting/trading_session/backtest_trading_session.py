from typing import Union, Sequence

from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class BacktestTradingSession(TradingSession):
    """
    Encapsulates the settings and components for carrying out a backtest session. Pulls for data every day.
    """

    def __init__(self, contract_ticker_mapper: ContractTickerMapper, start_date, end_date,
                 position_sizer: PositionSizer, data_handler: DataHandler, timer: SettableTimer,
                 notifiers: Notifiers, portfolio: Portfolio, events_manager: EventManager, monitor: BacktestMonitor,
                 broker: BacktestBroker, order_factory: OrderFactory):
        """
        Set up the backtest variables according to what has been passed in.
        """
        super().__init__()
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.contract_ticker_mapper = contract_ticker_mapper
        self.start_date = start_date
        self.end_date = end_date

        self.notifiers = notifiers

        self.event_manager = events_manager
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.position_sizer = position_sizer
        self.monitor = monitor
        self.timer = timer
        self.order_factory = order_factory
        self.broker = broker

    def use_data_preloading(self, tickers: Union[Ticker, Sequence[Ticker]], time_delta: RelativeDelta = None):
        if time_delta is None:
            time_delta = RelativeDelta(years=1)
        data_history_start = self.start_date - time_delta
        self.data_handler.use_data_bundle(tickers, PriceField.ohlcv(), data_history_start, self.end_date)


