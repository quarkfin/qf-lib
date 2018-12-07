from copy import deepcopy
from typing import Sequence

from qf_lib.backtesting.order.order import Order
from .position_sizer import PositionSizer


class PercentAtRiskPositionSizer(PositionSizer):
    """
    This PercentAtRiskPositionSizer is using a predefined "percentage at risk" value to size the positions.

    """

    def size_orders(self, initial_orders: Sequence[Order]) -> Sequence[Order]:
        # copying because the caller of this method expects to get a copy of an order
        return [deepcopy(initial_order) for initial_order in initial_orders]

        contracts = [self._contract_ticker_mapper.ticker_to_contract(ticker) for ticker in self._tickers]
        current_exposures = self._get_current_exposures(contracts)
        target_percentages_dict = {}
        stop_prices_dict = {}

        for ticker, contract in zip(self._tickers, contracts):
            signal = self._model.get_signal(ticker, current_exposures[contract])

            target_percentages_dict[contract] = self._calculate_target_percentage(signal.suggested_exposure)
            if self._use_stop_losses:
                stop_prices_dict[contract] = self._calculate_stop_price(signal.suggested_exposure, signal, ticker)

        market_orders = self._order_factory.target_percent_orders(target_percentages_dict, MarketOrder())

        self._broker.cancel_all_open_orders()
        if market_orders:
            self._place_market_orders(market_orders)
        if self._use_stop_losses:
            self._place_stop_orders(contracts, market_orders, stop_prices_dict)

    def _place_market_orders(self, market_orders):
        self._broker.place_orders(market_orders)

    def _place_stop_orders(self, contracts, market_orders, stop_prices_dict):
        stop_orders = []
        for contract in contracts:
            stop_quantity = self._get_open_positions_quantity(contract)
            stop_quantity += self._get_pending_positions_quantity(contract, market_orders)
            stop_orders += self._order_factory.orders({contract: -stop_quantity}, StopOrder(stop_prices_dict[contract]))
        if stop_orders:
            self._broker.place_orders(stop_orders)

    def _get_pending_positions_quantity(self, contract, market_orders):
        order = next((order for order in market_orders if order.contract == contract), None)
        if order is None:
            return 0
        return order.quantity

    def _get_open_positions_quantity(self, contract):
        positions = self._broker.get_positions()
        quantity = next((position.quantity() for position in positions if position.contract() == contract), 0)
        return quantity

    def _calculate_stop_price(self, curr_exposure, signal, ticker):
        current_price = self._data_handler.get_last_available_price(ticker)
        suggested_risk_level = signal.fraction_at_risk
        stop_price = (1 - suggested_risk_level * curr_exposure.value) * current_price
        return stop_price

    def _calculate_target_percentage(self, curr_exposure):
        if self._tickers_are_independent:
            target_percentage = curr_exposure.value / len(self._tickers)
        else:
            target_percentage = curr_exposure.value
        return target_percentage
