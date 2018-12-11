from abc import ABCMeta, abstractmethod
from itertools import groupby
from typing import Sequence

from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.orderfactory import OrderFactory


class PositionSizer(object, metaclass=ABCMeta):
    """
    The PositionSizer abstract class converts signals to orders with size specified
    """

    def __init__(self, broker: Broker, data_handler: DataHandler, order_factory: OrderFactory,
                 contract_ticker_mapper: ContractTickerMapper):
        self._broker = broker
        self._data_handler = data_handler
        self._order_factory = order_factory
        self._contract_ticker_mapper = contract_ticker_mapper

    def size_signals(self, signals: Sequence[Signal]) -> Sequence[Order]:
        """
        Based on the signals provided, creates a list of Orders where proper sizing has been applied
        """

        self._check_for_duplicates(signals)

        contracts = [self._contract_ticker_mapper.ticker_to_contract(signal.ticker) for signal in signals]
        orders = []

        for signal, contract in zip(signals, contracts):
            market_order = self._generate_market_order(contract, signal)
            stop_order = self._generate_stop_order(contract, signal, [market_order])

            if market_order is not None:
                orders.append(market_order)

            if stop_order is not None:
                orders.append(stop_order)

        return orders

    @abstractmethod
    def _generate_market_order(self, contract, signal) -> Order:
        raise NotImplementedError("Should implement _generate_market_order()")

    @abstractmethod
    def _generate_stop_order(self, contract, signal, market_orders: Sequence[Order]) -> Order:
        raise NotImplementedError("Should implement _generate_stop_order()")

    def _calculate_stop_price(self, signal: Signal):
        current_price = self._data_handler.get_last_available_price(signal.ticker)
        price_multiplier = (1 - signal.fraction_at_risk * signal.suggested_exposure.value)
        stop_price = price_multiplier * current_price
        return stop_price

    def _get_existing_position_quantity(self, contract):
        positions = self._broker.get_positions()
        quantity = next((position.quantity() for position in positions if position.contract() == contract), 0)
        return quantity

    def _check_for_duplicates(self, signals: Sequence[Signal]):
        sorted_signals = sorted(signals, key=lambda signal: signal.ticker)
        for ticker, signal_group in groupby(sorted_signals, lambda signal: signal.ticker):
            signal_list = list(signal_group)
            if len(signal_list) > 1:
                raise ValueError("More than one signal for ticker {}".format(ticker.as_string()))
