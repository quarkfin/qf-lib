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

from abc import ABCMeta, abstractmethod
from typing import List, Optional, Sequence

from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.position import Position


class Broker(object, metaclass=ABCMeta):
    @abstractmethod
    def get_portfolio_value(self) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        pass

    @abstractmethod
    def place_orders(self, orders: Sequence[Order]) -> Sequence[int]:
        pass

    @abstractmethod
    def get_open_orders(self)-> Optional[List[Order]]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: int):
        """
        Raises
        ------
        OrderCancellingException if Order wasn't cancelled
        """
        pass

    @abstractmethod
    def cancel_all_open_orders(self):
        pass
