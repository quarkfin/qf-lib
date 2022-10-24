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
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.signals.signals_register import SignalsRegister
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.data_provider import DataProvider


class PositionSizer(metaclass=ABCMeta):
    """ The PositionSizer abstract class converts signals to orders with size specified. """

    def __init__(self, broker: Broker, data_provider: DataProvider, order_factory: OrderFactory,
                 signals_register: SignalsRegister):
        self._broker = broker
        self._data_provider = data_provider
        self._order_factory = order_factory
        self._signals_register = signals_register
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def size_signals(self, signals: List[Signal], use_stop_losses: bool = True,
                     time_in_force: TimeInForce = TimeInForce.OPG, frequency: Frequency = None) -> List[Order]:
        """
        Based on the signals provided, creates a list of Orders where proper sizing has been applied

        Parameters
        -----------
        signals: List[Signal]
            list of signals,  based on which the orders will be created
        use_stop_losses: bool
            if true, for each MarketOrder generated for a signal, additionally a StopOrder will be created
        time_in_force: TimeInForce
            time in force, which will be used to create the Orders based on the provided Signals
        frequency: Frequency
            frequency of trading, further used to create Orders

        StopOrders details
        -------------------
        For each Market Order a Stop Order is generated if and only if the quantity in Market Order + position quantity
        for this ticker != 0. This means that StopOrders are not generated if the MarketOrder should completely close
        the position for the ticker.

        """

        signals = self._resolve_signal_duplicates(signals)
        updated_signals = self._remove_redundant_signals(signals)

        market_orders = self._generate_market_orders(updated_signals, time_in_force, frequency)
        market_orders = [order for order in market_orders if order is not None]

        orders = market_orders

        for order in market_orders:
            self.logger.info("Market Order for {}, {}".format(order.ticker, order))

        if use_stop_losses:
            # As the market orders are not sorted according to signals, create a dictionary mapping
            # tickers to market orders (orders contain now only these market orders which are not None)
            ticker_to_market_order = {
                order.ticker: order for order in market_orders
            }

            stop_orders = [
                self._generate_stop_order(signal, ticker_to_market_order)
                for signal in updated_signals if signal.suggested_exposure != Exposure.OUT
            ]

            stop_orders = [order for order in stop_orders if order is not None]
            orders = market_orders + stop_orders

            for order in stop_orders:
                self.logger.info("Stop Order for {}, {}".format(order.ticker, order))

        # Update strategy information inside the Orders
        def current_specific_ticker(ticker: Ticker):
            return ticker.get_current_specific_ticker() if isinstance(ticker, FutureTicker) else ticker

        ticker_to_alpha_model = {
            current_specific_ticker(signal.ticker): signal.alpha_model for signal in updated_signals
        }
        for order in orders:
            alpha_model = ticker_to_alpha_model[order.ticker]
            order.strategy = str(alpha_model)

        # The signals are saved at the very end of the function, so that in case if stop orders are being computed, it
        # is not necessary to filter out signals which happened after the <current time> in the _cap_stop_price
        self.logger.info("Position Sizer - Saving the signals")
        self._signals_register.save_signals(signals)

        return orders

    def _remove_redundant_signals(self, signals: List[Signal]) -> List[Signal]:
        """
        Remove all these signals, which do not need to be passed into order factory as they obviously do not change the
        state of the portfolio (current exposure equals Exposure.OUT and suggested exposure is also Exposure.OUT).
        """
        self.logger.info("Position Sizer - Removing redundant signals")
        specific_tickers_with_open_position = set(p.ticker() for p in self._broker.get_positions())

        def position_for_ticker_exists_in_portfolio(ticker: Ticker) -> bool:
            if isinstance(ticker, FutureTicker):
                # Check if any of specific tickers with open positions in portfolio belongs to tickers family
                return any([ticker.belongs_to_family(t) for t in specific_tickers_with_open_position])
            else:
                return ticker in specific_tickers_with_open_position

        redundant_signals = [signal for signal in signals
                             if signal.suggested_exposure == Exposure.OUT and
                             not position_for_ticker_exists_in_portfolio(signal.ticker)]

        new_signals = [s for s in signals if s not in redundant_signals]
        return new_signals

    @abstractmethod
    def _generate_market_orders(self, signals: List[Signal], time_in_force: TimeInForce, frequency: Frequency = None) \
            -> List[Optional[Order]]:
        raise NotImplementedError("Should implement _generate_market_orders()")

    def _generate_stop_order(self, signal, ticker_to_market_order: Dict[Ticker, Order]) -> Optional[Order]:
        """
        As each of the stop orders relies on the precomputed stop_price, which considers a.o. last available price of
        the security, orders are being created separately for each of the signals.
        """
        # stop_quantity = existing position size + recent market orders quantity
        stop_quantity = self._get_existing_position_quantity(signal.ticker)

        try:
            market_order = ticker_to_market_order[signal.ticker]
            stop_quantity += market_order.quantity
        except KeyError:
            # Generated Market Order was equal to None
            pass

        if stop_quantity != 0:
            stop_price = self._calculate_stop_price(signal)
            if not is_finite_number(stop_price):
                self.logger.info("Stop price should be a finite number")
                return None

            stop_price = self._cap_stop_price(stop_price, signal)

            # put minus before the quantity as stop order has to go in the opposite direction
            stop_orders = self._order_factory.orders({signal.ticker: -stop_quantity}, StopOrder(stop_price),
                                                     TimeInForce.GTC)

            assert len(stop_orders) == 1, "Only one order should be generated"
            return stop_orders[0]
        else:
            # quantity is 0 - no need to place a stop order
            return None

    def _cap_stop_price(self, stop_price: float, signal: Signal):
        """
        Prevent the stop price from moving down in case of a long position or up in case of a short position.

        Adjust the stop price only in case if there is an existing open position for specifically this ticker. E.g.
        in case if there exists an open position for the December Cotton future contract, which expired today, if
        we are creating an order for the January Cotton contract we should not adjust the StopOrders stop price.
        """
        # If there exist an open position for the ticker - check the previous Stop Order
        specific_ticker = signal.ticker.get_current_specific_ticker() \
            if isinstance(signal.ticker, FutureTicker) else signal.ticker

        position_quantity = self._get_existing_position_quantity(specific_ticker)

        if position_quantity != 0:
            # Get the last signal that was generated for the ticker
            signals_series = self._signals_register.get_signals_for_ticker(ticker=specific_ticker,
                                                                           alpha_model=signal.alpha_model)
            if not signals_series.empty:
                # Get the last signal, which was generated for the same exposure as the current exposure
                exposure_series = signals_series.apply(lambda s: s.suggested_exposure)
                current_exposure = Exposure.LONG if position_quantity > 0 else Exposure.SHORT
                last_date_with_current_exposure = exposure_series.where(exposure_series == current_exposure)\
                    .last_valid_index()
                if last_date_with_current_exposure is None:
                    self.logger.error("There is an open position for the ticker {} but no signal was found")
                    return stop_price

                last_signal_for_the_ticker = signals_series.loc[last_date_with_current_exposure]  # type: Signal
                previous_stop_price = self._calculate_stop_price(last_signal_for_the_ticker)

                if last_signal_for_the_ticker.suggested_exposure == Exposure.OUT or \
                        not is_finite_number(previous_stop_price):
                    return stop_price

                if last_signal_for_the_ticker.suggested_exposure == Exposure.LONG:
                    stop_price = max([stop_price, previous_stop_price])
                elif last_signal_for_the_ticker.suggested_exposure == Exposure.SHORT:
                    stop_price = min([stop_price, previous_stop_price])

        return stop_price

    def _calculate_stop_price(self, signal: Signal):
        current_price = signal.last_available_price
        assert is_finite_number(current_price), f"Signal generated for the {signal.symbol} does not contain " \
                                                f"last_available_price. In order to use the Position Sizer with " \
                                                f"stop_losses it is necessary for the signals to contain the last " \
                                                f"available price."

        price_multiplier = 1 - signal.fraction_at_risk * signal.suggested_exposure.value
        stop_price = price_multiplier * current_price
        stop_price = self._round_stop_price(stop_price)
        return stop_price

    def _get_existing_position_quantity(self, ticker: Ticker):
        positions = self._broker.get_positions()
        quantity = next((position.quantity() for position in positions if position.ticker() == ticker), 0)
        return quantity

    def _resolve_signal_duplicates(self, signals: List[Signal]):
        """
        This implementation only checks if there is one signal for given ticker.
        If more than one signal is present for given ticker it raises exception.
        It aims to prevent unintended behaviour of a strategy:
            for example if two alpha models give contradictory signals.
        In order to handle conflict resolution override _resolve_signal_duplicates() and implement your own logic.
        There is no single way to resolve duplicates
        """
        self.logger.info("Position Sizer - checking for signal duplicates")
        sorted_signals = sorted(signals, key=lambda signal: signal.ticker)
        for ticker, signal_group in groupby(sorted_signals, lambda signal: signal.ticker):
            signal_list = list(signal_group)
            if len(signal_list) > 1:
                raise ValueError(f"More than one signal for ticker {ticker.as_string()}. "
                                 f"Override _resolve_signal_duplicates() if you need to handle multiple signals")
        return signals

    @staticmethod
    def _get_specific_ticker(ticker: Ticker):
        return ticker.get_current_specific_ticker() if isinstance(ticker, FutureTicker) else ticker

    @staticmethod
    def _round_stop_price(stop_price: float) -> float:
        """
        The stop price has to be expressed in the format that matches the minimum price variation of a contract.
        For example 10.123 is not a valid stop price for a contract with minimum price variation of 0.01
        It is assumed that contracts have minimum price variation of 0.01 and the stop price is rounded to 2 decimals.
        """
        return round(stop_price, 2)
