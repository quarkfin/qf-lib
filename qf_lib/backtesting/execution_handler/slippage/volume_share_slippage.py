from typing import Sequence, Tuple

import numpy as np

from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.order.order import Order
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker


class VolumeShareSlippage(Slippage):
    """
    Slippage based on the daily volume of the traded assets. It can limit the Order's volume. The price slippage is
    calculated by multiplying no-slippage-price by (1 + volume-share^2 * self.price_impact).

    The direction of the slippage is always making the price worse for the trader (it increases the price when
    buying and decreases when selling).

    This model needs to know the daily volume of the traded asset, thus the model can be only applied at the end
    of the day, when the full bar for that day is already available.
    """

    def __init__(self, volume_share_limit: float, price_impact: float, data_handler: DataHandler,
                 contract_ticker_mapper: ContractTickerMapper):
        """
        Parameters
        ----------
        volume_share_limit
            number from range [0,1] which denotes how big (volume-wise) the Order can be i.e. if it's 0.5 and a daily
            volume for a given asset is 1,000,000 USD, then max volume of the Order can be 500,000 USD
        price_impact
            factor which implies how big will be the slippage
        data_handler
            DataHandler component
        contract_ticker_mapper
            ContractTickerMapper component
        """
        self.max_volume_share_limit = volume_share_limit
        self.price_impact = price_impact

        self.contract_ticker_mapper = contract_ticker_mapper
        self.data_handler = data_handler

    def apply_slippage(
        self, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float]
    ) -> Tuple[Sequence[float], Sequence[int]]:
        no_slippage_fill_prices = np.array(no_slippage_fill_prices)

        tickers = [self.contract_ticker_mapper.contract_to_ticker(order.contract) for order in orders]
        market_daily_volumes = self._get_volumes_from_today(tickers)

        order_volumes = np.array([order.quantity for order in orders])
        fill_volumes = self._get_fill_volumes(order_volumes, market_daily_volumes)

        # no need to use absolute numbers; it's squared later on
        volume_shares = fill_volumes / market_daily_volumes  # type: Sequence[float]

        abs_price_impact = volume_shares ** 2 * self.price_impact * no_slippage_fill_prices
        price_impact = np.copysign(abs_price_impact, order_volumes)
        slippage_prices = no_slippage_fill_prices + price_impact

        slippage_prices[fill_volumes == 0] = np.nan

        # limit should still hold

        return slippage_prices, fill_volumes

    def _get_volumes_from_today(self, tickers: Sequence[Ticker]):
        unique_tickers = list(set(tickers))
        today_bar = self.data_handler.get_bar_for_today(unique_tickers)
        volumes = today_bar.loc[tickers, PriceField.Volume].values

        return volumes

    def _get_fill_volumes(self, order_volumes, market_volumes):
        max_abs_order_volumes = market_volumes * self.max_volume_share_limit
        abs_order_volumes = np.absolute(order_volumes)

        abs_fill_volumes = np.minimum(abs_order_volumes, max_abs_order_volumes)
        fill_volumes = np.copysign(abs_fill_volumes, order_volumes)

        real_fill_volumes = np.floor(fill_volumes)

        return real_fill_volumes
