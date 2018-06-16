from typing import List, Optional, Sequence

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.execution_handler.execution_handler import ExecutionHandler
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.position import Position


class BacktestBroker(Broker):
    def __init__(self, portfolio: Portfolio, execution_handler: ExecutionHandler):
        self.portfolio = portfolio
        self.execution_handler = execution_handler

    def get_portfolio_value(self) -> Optional[float]:
        return self.portfolio.net_liquidation

    def get_positions(self) -> List[Position]:
        return list(self.portfolio.open_positions_dict.values())

    def place_orders(self, orders: Sequence[Order]) -> Sequence[int]:
        id_list = self.execution_handler.accept_orders(orders)
        return id_list

    def cancel_order(self, order_id: int):
        self.execution_handler.cancel_order(order_id)

    def get_open_orders(self)-> List[Order]:
        return self.execution_handler.get_open_orders()

    def cancel_all_open_orders(self):
        self.execution_handler.cancel_all_open_orders()
