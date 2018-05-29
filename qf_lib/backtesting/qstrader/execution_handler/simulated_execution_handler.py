import math
from collections import defaultdict
from typing import Dict, List, Sequence

from qf_lib.backtesting.qstrader.data_handler.data_handler import DataHandler
from qf_lib.backtesting.qstrader.events.event_manager import EventManager
from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent
from qf_lib.backtesting.qstrader.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.qstrader.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.qstrader.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.qstrader.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from .base import ExecutionHandler


class SimulatedExecutionHandler(ExecutionHandler):
    """
    The simulated execution handler which executes an order on the open of next bar.
    """

    def __init__(self, event_manager: EventManager, data_handler: DataHandler, timer: Timer,
                 scheduler: Scheduler, monitor: AbstractMonitor, commission_model: CommissionModel) -> None:
        scheduler.subscribe(MarketOpenEvent, self)

        self.event_manager = event_manager
        self.data_handler = data_handler
        self.timer = timer
        self.monitor = monitor
        self.commission_model = commission_model

        self.awaiting_orders = defaultdict(list)  # type: Dict[Ticker, List[Order]]

    def on_market_open(self, _: MarketOpenEvent):
        self._execute_orders()

    def accept_orders(self, orders: Sequence[Order]) -> None:
        """
        Appends Orders to a list of orders waiting to be carried out.
        """
        for order in orders:
            ticker = order.ticker
            self.awaiting_orders[ticker].append(order)

    def _execute_orders(self):
        """
        Converts Orders into FillEvents using Market Open prices
        """
        all_tickers_in_orders = list(self.awaiting_orders.keys())

        # obtain the current market open prices
        current_prices_series = self.data_handler.get_current_price(tickers=all_tickers_in_orders)

        unexecuted_orders = defaultdict(list)  # type: Dict[Ticker, List[Order]]

        for ticker, order_list in self.awaiting_orders.items():
            security_price = current_prices_series[ticker]  # Market open price for given security

            if math.isnan(security_price):
                unexecuted_orders[ticker] = order_list
            else:
                for order in order_list:
                    self._execute_order(order, security_price)

        self.awaiting_orders = unexecuted_orders

    def _execute_order(self, order: Order, security_price: float):
        """
        Simulates execution of single order by converting the Order into FillEvent.
        """
        # Obtain values from the OrderEvent
        timestamp = self.timer.now()
        ticker = order.ticker
        quantity = order.quantity

        # obtain the fill price
        fill_price = self._calculate_fill_price(order, security_price)

        # set a dummy exchange and calculate trade commission
        commission = self.commission_model.calculate_commission(quantity, fill_price)

        # create the FillEvent and place in the event manager
        fill_event = FillEvent(timestamp, ticker, quantity, fill_price, commission)
        self.event_manager.publish(fill_event)
        self.monitor.record_trade(fill_event)

    @staticmethod
    def _calculate_fill_price(_: Order, security_price: float) -> float:
        """
        Dummy fill price calculation. Take the market price
        """
        return security_price
