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
from typing import List

from qf_lib.backtesting.order.order import Order
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.data_provider import DataProvider


class OrdersFilter(metaclass=abc.ABCMeta):
    """Adjusts final orders list to meet various requirements e.g. volume limitations."""
    def __init__(self, data_provider: DataProvider):
        self._data_provider = data_provider

        self.logger = qf_logger.getChild(self.__class__.__name__)

    @abc.abstractmethod
    def adjust_orders(self, orders: List[Order]) -> List[Order]:
        """
        Takes the original produced list of orders and returns a new one, where all of the original orders are modified
        in order to meet the predefined requirements.
        """
        raise NotImplementedError()
