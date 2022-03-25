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

import numpy as np

from abc import ABCMeta, abstractmethod
from datetime import datetime
from itertools import groupby
from typing import Sequence, Tuple, Optional

from qf_lib.backtesting.order.order import Order
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.data_provider import DataProvider


class Slippage(metaclass=ABCMeta):
    """
    Base class for slippage models.
    It can limit the Order's volume. This model needs to know the daily volume of the traded asset, thus it uses the
    data provider in order to be able to access the volume value for the day.

    Parameters
    ----------
    data_provider: DataProvider
        DataProvider component
    max_volume_share_limit: float, None
        number from range [0,1] which denotes how big (volume-wise) the Order can be i.e. if it's 0.5 and a daily
        volume for a given asset is 1,000,000 USD, then max volume of the Order can be 500,000 USD. If not provided, no
        volume checks are performed.
    """

    def __init__(self, data_provider: DataProvider, max_volume_share_limit: Optional[float] = None):
        self.max_volume_share_limit = max_volume_share_limit
        self._data_provider = data_provider

        self._logger = qf_logger.getChild(self.__class__.__name__)

    def process_orders(self, date: datetime, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float]) -> \
            Tuple[Sequence[float], Sequence[float]]:
        """
        Calculates fill prices and quantities for Orders. For Orders that can't be executed (missing security price,
        etc.) float("nan") will be returned.

        Parameters
        ----------
        date: datetime
            time when the slippage is applied
        orders: Sequence[Order]
            sequence of Orders for which the fill price should be calculated
        no_slippage_fill_prices: Sequence[float]
            fill prices without a slippage applied. Each fill price corresponds to the Order from `orders` list

        Returns
        -------
        Tuple[Sequence[float], Sequence[float]]
            sequence of fill prices (order corresponds to the order of orders provided as an argument of the method),
            sequence of fill order quantities
        """

        self._check_for_duplicates(date, orders)

        # Compute the fill volumes for orders
        if self.max_volume_share_limit is not None:
            fill_volumes = self._get_fill_volumes(orders, date)
        else:
            fill_volumes = np.array([order.quantity for order in orders])

        fill_prices = self._get_fill_prices(date, orders, no_slippage_fill_prices, fill_volumes)
        return fill_prices, fill_volumes

    @abstractmethod
    def _get_fill_prices(self, date: datetime, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float],
                         fill_volumes: Sequence[int]) -> Sequence[float]:
        raise NotImplementedError()

    def _volumes_traded_today(self, date: datetime, tickers: Sequence[Ticker]) -> Sequence[int]:
        """
        For each ticker return the volume traded today. In case of lacking volume data - 0 is returned.
        """
        start_date = date + RelativeDelta(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + RelativeDelta(days=1)

        # Look into the future in order to see the total volume traded today
        volume_df = self._data_provider.get_price(tickers, PriceField.Volume, start_date, end_date, Frequency.DAILY)
        volume_df = volume_df.fillna(0.0)
        try:
            volumes = volume_df.loc[start_date, tickers].values
        except KeyError:
            volumes = np.repeat(0, len(tickers))

        # Replace negative values with 0
        volumes[volumes < 0] = 0
        return volumes

    def _get_fill_volumes(self, orders: Sequence[Order], date: datetime) -> Sequence[float]:
        """
        Compute the fill volumes, where the fill volume for each asset should fulfill the following:
        abs(fill_volume) <= self.max_volume_share_limit * volume_traded_today
        """
        order_volumes = np.array([order.quantity for order in orders])
        tickers = [order.ticker for order in orders]
        market_volumes = self._volumes_traded_today(date, tickers)

        max_abs_order_volumes = [volume * self.max_volume_share_limit for volume in market_volumes]
        abs_order_volumes = np.absolute(order_volumes)

        abs_fill_volumes = np.minimum(abs_order_volumes, max_abs_order_volumes)
        fill_volumes = np.copysign(abs_fill_volumes, order_volumes)

        fill_volumes = np.array([volume if order.ticker.security_type == SecurityType.CRYPTO else float(math.floor(volume))
                                 for volume, order in zip(fill_volumes, orders)])

        return fill_volumes

    def _check_for_duplicates(self, date: datetime, orders: Sequence[Order]):
        sorted_orders = sorted(orders, key=lambda order: order.ticker)
        for ticker, orders_group in groupby(sorted_orders, lambda order: order.ticker):
            orders_list = list(orders_group)
            if len(orders_list) > 1:
                self._logger.warning("{} More than one order for ticker {}:".format(date, ticker))
                for order in orders_list:
                    self._logger.warning(order)
