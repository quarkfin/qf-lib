from abc import ABCMeta, abstractmethod
from itertools import groupby
from typing import List, Sequence

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


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
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def size_signals(self, signals: Sequence[Signal]) -> List[Order]:
        """
        Based on the signals provided, creates a list of Orders where proper sizing has been applied
        """

        self._check_for_duplicates(signals)

        contracts = [self._contract_ticker_mapper.ticker_to_contract(signal.ticker) for signal in signals]
        orders = []

        for signal, contract in zip(signals, contracts):
            market_order = self._generate_market_order(contract, signal)
            if market_order is not None:
                orders.append(market_order)
                self.logger.info("Market Order for {}, {}".format(contract, market_order))
            else:
                self.logger.info("No Market Order for {}".format(contract))

            if signal.suggested_exposure != Exposure.OUT:
                stop_order = self._generate_stop_order(contract, signal, market_order)
                if stop_order is not None:
                    orders.append(stop_order)
                    self.logger.info("Stop Order for {}, {}".format(contract, stop_order))
                else:
                    self.logger.info("No Stop Order for {}".format(contract))

        return orders

    @abstractmethod
    def _generate_market_order(self, contract, signal: Signal) -> Order:
        raise NotImplementedError("Should implement _generate_market_order()")

    def _generate_stop_order(self, contract, signal, market_order: Order):
        # stop_quantity = existing position size + recent market orders quantity
        stop_quantity = self._get_existing_position_quantity(contract)

        if market_order is not None:
            stop_quantity += market_order.quantity

        if stop_quantity != 0:
            stop_price = self._calculate_stop_price(signal)
            assert is_finite_number(stop_price), "Stop price should be a finite number"

            # put minus before the quantity as stop order has to go in the opposite direction
            stop_orders = self._order_factory.orders({contract: -stop_quantity}, StopOrder(stop_price), TimeInForce.GTC)

            assert len(stop_orders) == 1, "Only one order should be generated"
            return stop_orders[0]
        else:
            # quantity is 0 - no need to place a stop order
            return None

    def _calculate_stop_price(self, signal: Signal):
        current_price = self._data_handler.get_last_available_price(signal.ticker)
        price_multiplier = 1 - signal.fraction_at_risk * signal.suggested_exposure.value
        stop_price = price_multiplier * current_price
        stop_price = self._round_stop_price(stop_price)
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

    @staticmethod
    def _round_stop_price(stop_price: float):
        """
        The stop price has to be expressed in the format that matches the minimum price variation of a contract.
        For example 10.123 is not a valid stop price for a contract with minimum price variation of 0.01
        It is assumed that contracts have minimum price variation of 0.01 and the stop price is rounded to 2 decimals.
        """
        return round(stop_price, 2)


