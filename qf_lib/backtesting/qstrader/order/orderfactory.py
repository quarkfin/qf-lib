import math
from typing import Sequence, Mapping

from qf_lib.backtesting.qstrader.data_handler.data_handler import DataHandler
from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.backtesting.qstrader.portfolio.portfolio import Portfolio
from qf_lib.common.tickers.tickers import Ticker


class OrderFactory(object):
    def __init__(self, portfolio: Portfolio, data_handler: DataHandler):
        self.portfolio = portfolio
        self.data_handler = data_handler

    def orders(self, quantities: Mapping[Ticker, int]) -> Sequence[Order]:
        """
        Creates a list of Orders for given numbers of shares for each given asset.

        Orders requiring 0 shares will be removed from resulting order list

        Parameters
        ----------
        quantities
            mapping of a ticker to an amount of shares which should be bought/sold.
            If number is positive then asset will be bought. Otherwise it will be sold.
        """
        order_list = [Order(ticker, quantity) for ticker, quantity in quantities.items() if quantity != 0]
        return order_list

    def target_orders(self, target_quantities: Mapping[Ticker, int]) -> Sequence[Order]:
        """
        Creates a list of Orders from a dictionary of desired target number of shares (number of shares which should be
        present in the portfolio after executing the Order).

        If the position doesn't already exist, the new Order is placed for the :target_quantity of shares.
        If the position does exist the Order for the difference between the target number of shares
        and the current number of shares is placed.

        Parameters
        ----------
        target_quantities
            mapping of a ticker to a target number of shares which should be present in the portfolio after the Order
            is executed.
        """
        quantities = dict()

        for ticker, target_quantity in target_quantities.items():
            position = self.portfolio.get_position(ticker)
            current_quantity = 0
            if position is not None:
                current_quantity = position.number_of_shares

            quantity = target_quantity - current_quantity
            quantities[ticker] = quantity

        return self.orders(quantities)

    def value_orders(self, values: Mapping[Ticker, float]) -> Sequence[Order]:
        """
        Creates a list of Orders by specifying the amount of money which should be spent on each asset rather
        than the number of shares to buy/sell.

        Parameters
        ----------
        values
            mapping of a ticker to the amount of money which should be spent on the asset (expressed in the currency
            in which the asset is traded)
        """
        quantities = self._calculate_shares_amounts(values)
        return self.orders(quantities)

    def percent_order(self, percentages: Mapping[Ticker, float]) -> Sequence[Order]:
        """
        Creates a list of Orders by specifying the percentage of the current portfolio value which should be spent
        on each asset.

        Parameters
        ----------
        percentages
            mapping of a ticker to a percentage value of the current portfolio which should be allocated in the asset.
            This is specified as a decimal value (e.g. 0.5 means 50%)
        """
        portfolio_value = self.portfolio.current_portfolio_value
        values = {ticker: portfolio_value * percent for ticker, percent in percentages.items()}

        return self.value_orders(values)

    def target_value_order(self, target_values: Mapping[Ticker, float]) -> Sequence[Order]:
        """
        Creates a list of Orders by specifying how much should be allocated in each asset after the Orders
        have been executed.

        Example:
            if we've already have 10M invested in 'SPY US Equity' and you call this method with target value of 11M
            then only 1M will be spent on this asset

        Parameters
        ----------
        target_values
            mapping of a ticker to a value which should be allocated in the asset after the Order has been executed
            (expressed in the currency in which the asset is traded)
        """
        target_quantities = self._calculate_shares_amounts(target_values)
        return self.target_orders(target_quantities)

    def order_target_percent(self, target_percentages: Mapping[Ticker, float]) -> Sequence[Order]:
        """
        Creates an Order adjusting a position to a value equal to the given percentage of the portfolio.

        Parameters
        ----------
        target_percentages
            mapping of a ticker to a percentage of a current portfolio value which should be allocated in each asset
            after the Order has been carried out
        """
        portfolio_value = self.portfolio.current_portfolio_value
        target_values = {
            ticker: portfolio_value * target_percent for ticker, target_percent in target_percentages.items()
        }
        return self.target_value_order(target_values)

    def _calculate_shares_amounts(self, values: Mapping[Ticker, float]) -> Mapping[Ticker, int]:
        tickers = list(values.keys())
        current_prices = self.data_handler.get_last_available_price(tickers)

        quantities = dict()
        for ticker, value in values.items():
            current_price = current_prices.loc[ticker]
            quantity = math.floor(value / current_price)  # type: int
            quantities[ticker] = quantity

        return quantities
