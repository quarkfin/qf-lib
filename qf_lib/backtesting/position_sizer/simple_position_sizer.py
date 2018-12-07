from typing import Sequence

from geneva_analytics.backtesting.alpha_models.signal import Signal
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order


class SimplePositionSizer(object):
    """
    This SimplePositionSizer converts signals to orders which are the size of 100% of the current portfolio value

    """

    def size_signals(self, signals: Sequence[Signal]) -> Sequence[Order]:

        contracts = [self._contract_ticker_mapper.ticker_to_contract(signal.ticker) for signal in signals]
        orders = []

        for signal, contract in zip(signals, contracts):
            market_order = self._generate_market_order(contract, signal)
            stop_order = self._generate_stop_order(contract, signal, market_order)

            orders.append(market_order)
            orders.append(stop_order)

        return orders

    def _generate_market_order(self, contract, signal):
        target_percentage = signal.suggested_exposure.value
        market_orders = self._order_factory.target_percent_orders({contract, target_percentage}, MarketOrder())

        assert len(market_orders) == 1, "Only one order should be generated"
        return market_orders[0]

    def _generate_stop_order(self, contract, signal, market_order: Order):
        stop_price = self._calculate_stop_price(signal)

        # stop_quantity = existing position size + recent market order quantity
        stop_quantity = self._get_existing_position_quantity(contract)
        stop_quantity += market_order.quantity
        stop_orders = self._order_factory.orders({contract: -stop_quantity}, StopOrder(stop_price))

        assert len(stop_orders) == 1, "Only one order should be generated"
        return stop_orders[0]

    def _calculate_stop_price(self, signal: Signal):
        current_price = self._data_handler.get_last_available_price(signal.ticker)
        price_multiplier = (1 - signal.fraction_at_risk * signal.suggested_exposure.value)
        stop_price = price_multiplier * current_price
        return stop_price

    def _get_existing_position_quantity(self, contract):
        positions = self._broker.get_positions()
        quantity = next((position.quantity() for position in positions if position.contract() == contract), 0)
        return quantity
