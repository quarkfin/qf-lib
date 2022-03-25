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
from datetime import datetime
from typing import Sequence, Optional

import numpy as np

from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.order.order import Order
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import cast_data_array_to_proper_type


class SquareRootMarketImpactSlippage(Slippage):
    """
    Slippage based on the square-root formula for market impact modelling.
    The price slippage is calculated by multiplying no-slippage-price by (1 + market impact), where the market impact is
    defined as the product of volatility, square of the volume and volatility ratio(volume traded in bar /
    average daily volume) and a constant value (price_impact).

    The direction of the slippage is always making the price worse for the trader (it increases the price when
    buying and decreases when selling).

    Parameters
    ----------
    price_impact: float
        factor which implies how big will be the slippage
    data_provider: DataProvider
        DataProvider component
    max_volume_share_limit: float, None
        number from range [0,1] which denotes how big (volume-wise) the Order can be i.e. if it's 0.5 and a daily
        volume for a given asset is 1,000,000 USD, then max volume of the Order can be 500,000 USD. If not provided, no
        volume checks are performed.
    """
    def __init__(self, price_impact: float, data_provider: DataProvider, max_volume_share_limit: Optional[float] = None):

        super().__init__(data_provider, max_volume_share_limit)

        self.price_impact = price_impact
        self._number_of_samples = 20

    def _get_fill_prices(self, date: datetime, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float],
                         fill_volumes: Sequence[float]) -> Sequence[float]:
        no_slippage_fill_prices = np.array(no_slippage_fill_prices)

        tickers = [order.ticker for order in orders]
        market_impact_values = self._compute_market_impact(date, tickers, fill_volumes)
        fill_prices = no_slippage_fill_prices * np.add(market_impact_values, 1.0)

        return fill_prices

    def _compute_market_impact(self, date: datetime, tickers: Sequence[Ticker], fill_volumes: Sequence[float]) \
            -> Sequence[float]:
        """
        Market Impact is positive for buys and negative for sells.
        MI = +/- price_impact * volatility * sqrt (fill volume / average daily volume)
        """
        start_date = date - RelativeDelta(days=60)
        end_date = date - RelativeDelta(days=1)

        # Download close price and volume values
        data_array = self._data_provider.get_price(tickers, [PriceField.Close, PriceField.Volume],
                                                   start_date, end_date, Frequency.DAILY)

        close_prices = cast_data_array_to_proper_type(data_array.loc[:, tickers, PriceField.Close])
        volumes = cast_data_array_to_proper_type(data_array.loc[:, tickers, PriceField.Volume])
        close_prices_volatility = close_prices.apply(self._compute_volatility).values

        average_volumes = volumes.apply(self._compute_average_volume).values

        abs_fill_volumes = np.abs(fill_volumes)
        volatility_volume_ratio = np.divide(abs_fill_volumes, average_volumes)
        sqrt_volatility_volume_ratio = np.sqrt(volatility_volume_ratio) * np.sign(fill_volumes)
        return self.price_impact * close_prices_volatility * sqrt_volatility_volume_ratio

    def _compute_volatility(self, prices_tms) -> float:
        """Compute the annualised volatility of the last self._number_of_samples days"""
        prices_tms = prices_tms.dropna().iloc[-self._number_of_samples:]
        prices_tms = PricesSeries(prices_tms)
        try:
            volatility = get_volatility(prices_tms, frequency=Frequency.DAILY, annualise=True)
        except (AssertionError, AttributeError):
            volatility = float('nan')
        return volatility

    def _compute_average_volume(self, volume_tms) -> float:
        """Compute the average volume of the last self._number_of_samples days"""
        volume_tms = volume_tms.dropna().iloc[-self._number_of_samples:]
        volume_tms = volume_tms[volume_tms >= 0]
        adv = volume_tms.mean()
        return adv
