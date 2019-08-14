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
from typing import Sequence, Tuple

from qf_lib.backtesting.order.order import Order


class Slippage(object, metaclass=ABCMeta):

    @abstractmethod
    def apply_slippage(
        self, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float]
    ) -> Tuple[Sequence[float], Sequence[int]]:
        """
        Calculates fill prices for Orders. For Orders that can't be executed (missing security price, etc.) float("nan")
        will be returned.

        Parameters
        ----------
        orders
            sequence of Orders for which the fill price should be calculated
        no_slippage_fill_prices
            fill prices without a slippage applied. Each fill price corresponds to the Order from `orders` list

        Returns
        -------
        sequence of fill prices (order corresponds to the order of orders provided as an argument of the method)
        """
        pass
