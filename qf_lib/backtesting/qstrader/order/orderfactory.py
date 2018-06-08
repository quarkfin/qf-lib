import math
from typing import Sequence, Mapping, Dict

from qf_lib.backtesting.qstrader.broker.broker import Broker
from qf_lib.backtesting.qstrader.contract.contract import Contract
from qf_lib.backtesting.qstrader.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.qstrader.data_handler.data_handler import DataHandler
from qf_lib.backtesting.qstrader.order.execution_style import ExecutionStyle
from qf_lib.backtesting.qstrader.order.order import Order


class OrderFactory(object):
    def __init__(self, broker: Broker, data_handler: DataHandler, contract_to_ticker_mapper: ContractTickerMapper):
        self.broker = broker
        self.data_handler = data_handler
        self.contract_to_ticker_mapper = contract_to_ticker_mapper

    def orders(self, quantities: Mapping[Contract, int], execution_style: ExecutionStyle, time_in_force: str)\
            -> Sequence[Order]:
        """
        Creates a list of Orders for given numbers of shares for each given asset.

        Orders requiring 0 shares will be removed from resulting order list

        Parameters
        ----------
        quantities
            mapping of a Contract to an amount of shares which should be bought/sold.
            If number is positive then asset will be bought. Otherwise it will be sold.
        execution_style
            execution style of an order (e.g. MarketOrder, StopOrder, etc.)
        time_in_force
            e.g. 'DAY' (Order valid for one trading session), 'GTC' (good till cancelled)
        """
        order_list = []
        for contract, quantity in quantities.items():
            if quantity != 0:
                order_list.append(Order(contract, quantity, execution_style, time_in_force))

        return order_list

    def target_orders(self, target_quantities: Mapping[Contract, int], execution_style: ExecutionStyle,
                      time_in_force: str) -> Sequence[Order]:
        """
        Creates a list of Orders from a dictionary of desired target number of shares (number of shares which should be
        present in the portfolio after executing the Order).

        If the position doesn't already exist, the new Order is placed for the :target_quantity of shares.
        If the position does exist the Order for the difference between the target number of shares
        and the current number of shares is placed.

        Parameters
        ----------
        target_quantities
            mapping of a Contract to a target number of shares which should be present in the portfolio after the Order
            is executed
        execution_style
            execution style of an order (e.g. MarketOrder, StopOrder, etc.)
        time_in_force
            e.g. 'DAY' (Order valid for one trading session), 'GTC' (good till cancelled)
        """
        quantities = dict()

        contract_to_positions = {position.contract(): position for position in self.broker.get_positions()}

        for contract, target_quantity in target_quantities.items():
            position = contract_to_positions.get(contract, None)
            current_quantity = 0
            if position is not None:
                current_quantity = position.quantity()

            quantity = target_quantity - current_quantity
            quantities[contract] = quantity

        return self.orders(quantities, execution_style, time_in_force)

    def value_orders(self, values: Mapping[Contract, float], execution_style: ExecutionStyle, time_in_force: str)\
            -> Sequence[Order]:
        """
        Creates a list of Orders by specifying the amount of money which should be spent on each asset rather
        than the number of shares to buy/sell.

        Parameters
        ----------
        values
            mapping of a Contract to the amount of money which should be spent on the asset (expressed in the currency
            in which the asset is traded)
        execution_style
            execution style of an order (e.g. MarketOrder, StopOrder, etc.)
        time_in_force
            e.g. 'DAY' (Order valid for one trading session), 'GTC' (good till cancelled)
        """
        quantities = self._calculate_shares_amounts(values)
        return self.orders(quantities, execution_style, time_in_force)

    def percent_order(self, percentages: Mapping[Contract, float], execution_style: ExecutionStyle, time_in_force: str)\
            -> Sequence[Order]:
        """
        Creates a list of Orders by specifying the percentage of the current portfolio value which should be spent
        on each asset.

        Parameters
        ----------
        percentages
            mapping of a Contract to a percentage value of the current portfolio which should be allocated in the asset.
            This is specified as a decimal value (e.g. 0.5 means 50%)
        execution_style
            execution style of an order (e.g. MarketOrder, StopOrder, etc.)
        time_in_force
            e.g. 'DAY' (Order valid for one trading session), 'GTC' (good till cancelled)
        """
        portfolio_value = self.broker.get_portfolio_value()
        values = {contract: portfolio_value * fraction for contract, fraction in percentages.items()}

        return self.value_orders(values, execution_style, time_in_force)

    def target_value_order(self, target_values: Mapping[Contract, float], execution_style: ExecutionStyle,
                           time_in_force: str) -> Sequence[Order]:
        """
        Creates a list of Orders by specifying how much should be allocated in each asset after the Orders
        have been executed.

        Example:
            if we've already have 10M invested in 'SPY US Equity' and you call this method with target value of 11M
            then only 1M will be spent on this asset

        Parameters
        ----------
        target_values
            mapping of a Contract to a value which should be allocated in the asset after the Order has been executed
            (expressed in the currency in which the asset is traded)
        execution_style
            execution style of an order (e.g. MarketOrder, StopOrder, etc.)
        time_in_force
            e.g. 'DAY' (Order valid for one trading session), 'GTC' (good till cancelled)
        """
        target_quantities = self._calculate_shares_amounts(target_values)
        return self.target_orders(target_quantities, execution_style, time_in_force)

    def order_target_percent(self, target_percentages: Mapping[Contract, float], execution_style: ExecutionStyle,
                             time_in_force: str) -> Sequence[Order]:
        """
        Creates an Order adjusting a position to a value equal to the given percentage of the portfolio.

        Parameters
        ----------
        target_percentages
            mapping of a Contract to a percentage of a current portfolio value which should be allocated in each asset
            after the Order has been carried out
        execution_style
            execution style of an order (e.g. MarketOrder, StopOrder, etc.)
        time_in_force
            e.g. 'DAY' (Order valid for one trading session), 'GTC' (good till cancelled)
        """
        portfolio_value = self.broker.get_portfolio_value()
        target_values = {
            contract: portfolio_value * target_percent for contract, target_percent in target_percentages.items()
        }
        return self.target_value_order(target_values, execution_style, time_in_force)

    def _calculate_shares_amounts(self, contract_to_amount_of_money: Mapping[Contract, float])\
            -> Mapping[Contract, int]:
        """
        Calculates how many shares can be bought for the given amount of money (value).
        """
        tickers_to_contract_and_amount_of_money = self._make_tickers_to_contract_and_amount_of_money(
            contract_to_amount_of_money)

        tickers = list(tickers_to_contract_and_amount_of_money.keys())
        current_prices = self.data_handler.get_last_available_price(tickers)

        quantities = dict()  # type: Dict[Contract, int]
        for ticker, (contract, amount_of_money) in tickers_to_contract_and_amount_of_money.items():
            current_price = current_prices.loc[ticker]
            quantity = math.floor(amount_of_money / current_price)  # type: int
            quantities[contract] = quantity

        return quantities

    def _make_tickers_to_contract_and_amount_of_money(self, contract_to_amount_of_money):
        tickers_to_contract_and_amount_of_money = dict()

        for contract, amount_of_money in contract_to_amount_of_money.items():
            ticker = self.contract_to_ticker_mapper.contract_to_ticker(contract)
            tickers_to_contract_and_amount_of_money[ticker] = contract, amount_of_money

        return tickers_to_contract_and_amount_of_money
