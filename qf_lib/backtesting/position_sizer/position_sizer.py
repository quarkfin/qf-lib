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

from abc import ABCMeta, abstractmethod
from itertools import groupby
from typing import List, Optional, Dict

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
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

    def size_signals(self, signals: List[Signal], use_stop_losses: bool = True) -> List[Order]:
        """
        Based on the signals provided, creates a list of Orders where proper sizing has been applied
        """

        self._check_for_duplicates(signals)

        market_orders = self._generate_market_orders(signals)
        market_orders = [order for order in market_orders if order is not None]

        orders = market_orders

        for order in market_orders:
            self.logger.info("Market Order for {}, {}".format(order.contract, order))

        if use_stop_losses:
            # As the market orders are not sorted according to signals, create a dictionary mapping
            # contracts to market orders (orders contain now only these market orders which are not None)
            contract_to_market_order = {
                order.contract: order for order in market_orders
            }

            stop_orders = [
                self._generate_stop_order(signal, contract_to_market_order)
                for signal in signals if signal.suggested_exposure != Exposure.OUT
            ]

            stop_orders = [order for order in stop_orders if order is not None]
            orders = market_orders + stop_orders

            for order in stop_orders:
                    self.logger.info("Stop Order for {}, {}".format(order.contract, order))

        return orders

    @abstractmethod
    def _generate_market_orders(self, signals: List[Signal]) -> List[Optional[Order]]:
        raise NotImplementedError("Should implement _generate_market_orders()")

    def _generate_stop_order(self, signal, contract_to_market_order: Dict[Contract, Order]) -> Optional[Order]:
        """
        As each of the stop orders relies on the precomputed stop_price, which considers a.o. last available price of
        the security, orders are being created separately for each of the signals.
        """
        contract = self._contract_ticker_mapper.ticker_to_contract(signal.ticker)

        # stop_quantity = existing position size + recent market orders quantity
        stop_quantity = self._get_existing_position_quantity(contract)

        try:
            market_order = contract_to_market_order[contract]
            stop_quantity += market_order.quantity
        except KeyError:
            # Generated Market Order was equal to None
            pass

        if stop_quantity != 0:
            stop_price = self._calculate_stop_price(signal)
            if not is_finite_number(stop_price):
                self.logger.info("Stop price should be a finite number")
                return None

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

    def _check_for_duplicates(self, signals: List[Signal]):
        sorted_signals = sorted(signals, key=lambda signal: signal.ticker)
        for ticker, signal_group in groupby(sorted_signals, lambda signal: signal.ticker):
            signal_list = list(signal_group)
            if len(signal_list) > 1:
                raise ValueError("More than one signal for ticker {}".format(ticker.as_string()))

    @staticmethod
    def _round_stop_price(stop_price: float) -> float:
        """
        The stop price has to be expressed in the format that matches the minimum price variation of a contract.
        For example 10.123 is not a valid stop price for a contract with minimum price variation of 0.01
        It is assumed that contracts have minimum price variation of 0.01 and the stop price is rounded to 2 decimals.
        """
        return round(stop_price, 2)
