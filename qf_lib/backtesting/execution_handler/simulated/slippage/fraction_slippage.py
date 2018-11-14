import math
from typing import Sequence

from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order


class FractionSlippage(Slippage):
    """
    Calculates the slippage by using some fixed fraction of the current securities' price (e.g. always 0.01%).
    """

    def __init__(self, slippage_rate: float, data_handler: DataHandler, contract_ticker_mapper: ContractTickerMapper):
        self.data_handler = data_handler
        self.contract_ticker_mapper = contract_ticker_mapper
        self.slippage_rate = slippage_rate

    def calc_fill_prices(self, orders: Sequence[Order]) -> Sequence[float]:
        tickers = [self.contract_ticker_mapper.contract_to_ticker(order.contract) for order in orders]
        unique_tickers = list(set(tickers))
        current_prices_series = self.data_handler.get_current_price(unique_tickers)

        fill_prices = []

        for order, ticker in zip(orders, tickers):
            if isinstance(order.execution_style, MarketOrder):
                current_price = current_prices_series[ticker]
                fill_price = self._get_single_fill_price(order, current_price)
            else:
                # TODO support StopOrders
                fill_price = float("nan")

            fill_prices.append(fill_price)

        return fill_prices

    def _get_single_fill_price(self, order, current_price):
        if math.isnan(current_price):
            fill_price = float('nan')
        else:
            if order.quantity > 0:  # BUY Order
                multiplier = 1 + self.slippage_rate
            else:  # SELL Order
                multiplier = 1 - self.slippage_rate

            fill_price = current_price * multiplier
        return fill_price




