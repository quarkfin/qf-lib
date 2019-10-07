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

import abc
from typing import Sequence, List

from qf_lib.backtesting.order.order import Order


class ExecutionHandler(metaclass=abc.ABCMeta):
    """
    The ExecutionHandler abstract class handles the interaction
    between a set of order objects and the set of Transaction
    objects that actually occur in the market.

    The handlers can be used to subclass simulated brokerages
    or live brokerages, with identical interfaces. This allows
    strategies to be backtested in a very similar manner to the
    live trading engine.

    ExecutionHandler can link to an optional Compliance component
    for simple record-keeping, which will keep track of all executed
    orders.
    """

    @abc.abstractmethod
    def assign_order_ids(self, orders: Sequence[Order]) -> List[int]:
        """
        Takes an Order and executes it producing an Transaction.

        Returns
        -------
        list of IDs of the Orders scheduled for execution
        """
        raise NotImplementedError("Should implement assign_order_ids()")

    @abc.abstractmethod
    def cancel_order(self, order_id: int) -> None:
        """
        Cancels the order with a given ID.

        Raises
        ------
        OrderCancellingException if Order wasn't cancelled
        """
        raise NotImplementedError("Should implement cancel_order()")

    @abc.abstractmethod
    def get_open_orders(self) -> List[Order]:
        """
        Returns
        -------
        the list of all Open orders
        """
        raise NotImplementedError("Should implement get_open_orders()")

    @abc.abstractmethod
    def cancel_all_open_orders(self) -> None:
        """
        Cancel all open Orders.
        """
        raise NotImplementedError("Should implement cancel_all_open_orders()")
