import math
from itertools import count
from typing import Dict, List, Sequence

from qf_lib.backtesting.qstrader.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.qstrader.data_handler.data_handler import DataHandler
from qf_lib.backtesting.qstrader.events.event_manager import EventManager
from qf_lib.backtesting.qstrader.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.qstrader.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.qstrader.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.qstrader.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.common.exceptions.broker_exceptions import OrderCancellingException
from qf_lib.backtesting.qstrader.order_fill import OrderFill
from qf_lib.backtesting.qstrader.portfolio.portfolio import Portfolio
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from .execution_handler import ExecutionHandler


class SimulatedExecutionHandler(ExecutionHandler):
    """
    The simulated execution handler which executes an order on the open of next bar.
    """

    def __init__(self, event_manager: EventManager, data_handler: DataHandler, timer: Timer,
                 scheduler: Scheduler, monitor: AbstractMonitor, commission_model: CommissionModel,
                 contracts_to_tickers_mapper: ContractTickerMapper, portfolio: Portfolio) -> None:
        scheduler.subscribe(MarketOpenEvent, self)

        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.event_manager = event_manager
        self.data_handler = data_handler
        self.timer = timer
        self.monitor = monitor
        self.commission_model = commission_model
        self.contracts_to_tickers_mapper = contracts_to_tickers_mapper
        self.portfolio = portfolio

        self._awaiting_orders = {}  # type: Dict[int, Order]
        self._order_id_generator = count(start=1)

    def on_market_open(self, _: MarketOpenEvent):
        if self._awaiting_orders:
            self._execute_orders()

    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        """
        Appends Orders to a list of Orders waiting to be carried out.
        """
        order_id_list = []
        for order in orders:
            order.id = self._get_next_order_id()
            order.order_state = "Awaiting"

            order_id_list.append(order.id)
            self._awaiting_orders[order.id] = order

        return order_id_list

    def cancel_order(self, order_id: int) -> bool:
        # if order_id is in the awaiting orders its id will be returned, otherwise: None will be returned
        try:
            del self._awaiting_orders[order_id]
        except KeyError:
            raise OrderCancellingException("Order of id: {:d} wasn't found in the list of awaiting Orders")

    def get_open_orders(self) -> List[Order]:
        return list(self._awaiting_orders.values())

    def cancel_all_open_orders(self):
        self._awaiting_orders.clear()

    def _get_next_order_id(self) -> int:
        return next(self._order_id_generator)

    def _execute_orders(self):
        """
        Converts Orders into OrderFills.
        """
        all_contracts = [order.contract for order in self._awaiting_orders.values()]
        contracts_to_tickers = {
            contract: self.contracts_to_tickers_mapper.contract_to_ticker(contract) for contract in all_contracts
        }

        all_tickers = list(contracts_to_tickers.values())
        current_prices_series = self.data_handler.get_current_price(tickers=all_tickers)
        unexecuted_orders_dict = {}  # type: Dict[int, Order]

        for order in self._awaiting_orders.values():
            ticker = contracts_to_tickers[order.contract]
            security_price = current_prices_series[ticker]

            if math.isnan(security_price):
                unexecuted_orders_dict[order.id] = order
            else:
                self._execute_order(order, security_price)

        self._awaiting_orders = unexecuted_orders_dict

    def _execute_order(self, order: Order, security_price: float):
        """
        Simulates execution of a single Order by converting the Order into OrderFill.
        """
        # obtain values from the OrderEvent
        timestamp = self.timer.now()
        contract = order.contract
        quantity = order.quantity

        # obtain the fill price
        fill_price = self._calculate_fill_price(order, security_price)

        # set a dummy exchange and calculate trade commission
        commission = self.commission_model.calculate_commission(quantity, fill_price)

        # create the OrderFill and update Portfolio
        order_fill = OrderFill(timestamp, contract, quantity, fill_price, commission)
        self.monitor.record_trade(order_fill)

        self.logger.info("Order executed. OrderFill has been created:\n{:s}".format(str(order_fill)))
        self.portfolio.transact_order_fill(order_fill)

    @staticmethod
    def _calculate_fill_price(_: Order, security_price: float) -> float:
        """
        Dummy fill price calculation. Take the market price
        """
        return security_price
