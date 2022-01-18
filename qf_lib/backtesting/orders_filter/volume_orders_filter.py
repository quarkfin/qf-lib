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
import math
from typing import List, Optional, Tuple

import numpy as np

from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.orders_filter.orders_filter import OrdersFilter
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.data_provider import DataProvider


class VolumeOrdersFilter(OrdersFilter):
    """ Verifies whether the orders sizes do not exceed the given volume limit.

    Parameters
    -----------
    data_provider: DataProvider
        used to download the volume data
    volume_percentage_limit: float
        defines the maximum percentage of the volume value, that the orders size should not exceed
    """

    def __init__(self, data_provider: DataProvider, volume_percentage_limit: float):
        super().__init__(data_provider)
        self._volume_percentage_limit = volume_percentage_limit

    def adjust_orders(self, orders: List[Order]) -> List[Order]:
        """ Takes list of orders and based on them creates a new list with orders, whose size does not to exceed the
        given volume limits. The Orders are changed in place.

        Parameters
        ----------
        orders: List[Order]
            list of orders to adjust

        Returns
        --------
        List[Order]
            list of orders, that do not exceed the given volume percentage limit
        """
        tickers = [order.ticker for order in orders]
        try:
            volume_df = self._data_provider.historical_price(tickers, PriceField.Volume, 5, frequency=Frequency.DAILY)

            # The stop orders will be adjusted only along with corresponding market orders
            stop_orders_dict = {order.ticker: order for order in orders if isinstance(order.execution_style, StopOrder)}
            adjusted_orders_tuples = [self._adjust_quantity(order, stop_orders_dict.get(order.ticker, None), volume_df)
                                      for order in orders if not isinstance(order.execution_style, StopOrder)]

            # Flatten the list of orders tuples
            adjusted_orders = [order for orders_tuple in adjusted_orders_tuples
                               for order in orders_tuple if order is not None and order.quantity != 0]

            return adjusted_orders
        except ValueError as e:
            self.logger.warning(f"VolumeOrdersFilter: orders cannot be adjusted due to the following reason: {e}",
                                stack_info=True)
            return orders

    def _adjust_quantity(self, order: Order, stop_order: Optional[Order], volume_df: QFDataFrame) -> \
            Tuple[Order, Order]:
        """Returns order with adjusted quantity if applicable."""
        ticker = order.ticker

        def average_past_volume(ticker: Ticker) -> Optional[float]:
            volume_series = volume_df[ticker]
            volume_series = volume_series.dropna()
            volume_series = volume_series[volume_series >= 0]
            return volume_series.mean()

        past_volume = average_past_volume(ticker)

        if is_finite_number(past_volume):
            volume_limit: int = math.floor(past_volume * self._volume_percentage_limit)

            # Check if the order quantity exceeds the limit
            if abs(order.quantity) > volume_limit:
                final_quantity = volume_limit * np.sign(order.quantity)
                adjustment_difference = final_quantity - order.quantity

                self.logger.info("VolumeOrdersFilter: Quantity change {} "
                                 "\n\tfinal quantity: {}".format(order, final_quantity))
                order.quantity = final_quantity

                if stop_order:
                    # Adjust the corresponding stop order
                    stop_order_final_quantity = stop_order.quantity - adjustment_difference
                    self.logger.info("VolumeOrdersFilter: Quantity change {} "
                                     "\n\tfinal quantity: {}".format(stop_order, final_quantity))
                    stop_order.quantity = stop_order_final_quantity

        return order, stop_order

    def __str__(self):
        return 'VolumeOrdersFilter:\n' \
               '\tvolume_percentage_limit: {}\n'.format(self._volume_percentage_limit)
