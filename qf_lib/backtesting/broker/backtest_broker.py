#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from typing import List, Optional, Sequence

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.execution_handler.execution_handler import ExecutionHandler
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.position import Position


class BacktestBroker(Broker):
    def __init__(self, contract_ticker_mapper: ContractTickerMapper, portfolio: Portfolio,
                 execution_handler: ExecutionHandler):
        super().__init__(contract_ticker_mapper)
        self.portfolio = portfolio
        self.execution_handler = execution_handler

    def get_portfolio_value(self) -> Optional[float]:
        return self.portfolio.net_liquidation

    def get_positions(self) -> List[Position]:
        return list(self.portfolio.open_positions_dict.values())

    def place_orders(self, orders: Sequence[Order]) -> Sequence[int]:
        id_list = self.execution_handler.assign_order_ids(orders)
        return id_list

    def cancel_order(self, order_id: int):
        self.execution_handler.cancel_order(order_id)

    def get_open_orders(self) -> List[Order]:
        return self.execution_handler.get_open_orders()

    def cancel_all_open_orders(self):
        self.execution_handler.cancel_all_open_orders()
