from typing import List, Optional

from qf_lib.backtesting.qstrader.broker.broker import Broker
from qf_lib.backtesting.qstrader.execution_handler.execution_handler import ExecutionHandler
from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.backtesting.qstrader.portfolio.portfolio import Portfolio
from qf_lib.backtesting.qstrader.portfolio.position import Position


class BacktestBroker(Broker):
    def __init__(self, portfolio: Portfolio, execution_handler: ExecutionHandler):
        self.portfolio = portfolio
        self.execution_handler = execution_handler

    def get_portfolio_value(self) -> Optional[float]:
        return self.portfolio.current_portfolio_value

    def get_positions(self) -> List[Position]:
        return list(self.portfolio.open_positions_dict.values())

    def place_order(self, order: Order) -> int:
        id_list = self.execution_handler.accept_orders([order])
        return id_list[0]

    def cancel_order(self, order_id: int):
        self.execution_handler.cancel_order(order_id)

    def get_open_orders(self)-> List[Order]:
        return self.execution_handler.get_open_orders()

    def cancel_all_open_orders(self):
        self.execution_handler.cancel_all_open_orders()


