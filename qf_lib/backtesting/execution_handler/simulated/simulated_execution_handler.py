from itertools import count, groupby
from typing import List, Sequence

from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.execution_handler.execution_handler import ExecutionHandler
from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated.market_orders_executor import MarketOrdersExecutor
from qf_lib.backtesting.execution_handler.simulated.stop_orders_executor import StopOrdersExecutor
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder, MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.common.exceptions.broker_exceptions import OrderCancellingException
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class SimulatedExecutionHandler(ExecutionHandler):
    """
    The simulated execution handler which executes an Order on the open of next bar, unless it is the ExecutionStyle
    is the StopOrder. Then the Order is executed if the Low field for the price is lower then the limit of that Order.
    StopOrders are executed at the MarketClose (if applicable) with the Low price.
    """

    def __init__(self, data_handler: DataHandler, timer: Timer,
                 scheduler: Scheduler, monitor: AbstractMonitor, commission_model: CommissionModel,
                 contracts_to_tickers_mapper: ContractTickerMapper, portfolio: Portfolio) -> None:
        scheduler.subscribe(MarketOpenEvent, self)

        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.data_handler = data_handler
        self.timer = timer
        self.commission_model = commission_model
        self.contracts_to_tickers_mapper = contracts_to_tickers_mapper
        self.portfolio = portfolio

        order_id_generator = count(start=1)

        self._market_orders_executor = MarketOrdersExecutor(
            contracts_to_tickers_mapper, data_handler, commission_model, monitor, portfolio, timer, order_id_generator
        )

        self._stop_orders_executor = StopOrdersExecutor(contracts_to_tickers_mapper, data_handler, order_id_generator,
                                                        commission_model, monitor, portfolio, timer)

    def on_market_close(self, _: MarketCloseEvent):
        self._stop_orders_executor.execute_orders()

    def on_market_open(self, _: MarketOpenEvent):
        self._market_orders_executor.execute_orders()

    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        """
        Appends Orders to a list of Orders waiting to be carried out.
        """
        order_id_list = []

        for order_style_type, orders_list in groupby(orders, lambda x: type(x.execution_style)):
            if order_style_type == MarketOrder:
                partial_order_id_list = self._market_orders_executor.accept_orders(orders_list)
            elif order_style_type == StopOrder:
                partial_order_id_list = self._stop_orders_executor.accept_orders(orders_list)
            else:
                raise ValueError("Unsupported ExecutionStyle: {}".format(order_style_type))

            order_id_list += partial_order_id_list

        return order_id_list

    def cancel_order(self, order_id: int):
        # if order_id is in the awaiting orders its id will be returned, otherwise: None will be returned
        removed_order = self._market_orders_executor.cancel_order(order_id)

        if removed_order is not None:
            return

        removed_order = self._stop_orders_executor.cancel_order(order_id)

        if removed_order is not None:
            return

        raise OrderCancellingException("Order of id: {:d} wasn't found in the list of awaiting Orders")

    def get_open_orders(self) -> List[Order]:
        return self._market_orders_executor.get_open_orders() + self._stop_orders_executor.get_open_orders()

    def cancel_all_open_orders(self):
        self._market_orders_executor.cancel_all_open_orders()
        self._stop_orders_executor.cancel_all_open_orders()

    @classmethod
    def _calculate_fill_price(cls, _: Order, security_price: float) -> float:
        """
        Dummy fill price calculation. Take the market price
        """
        return security_price
