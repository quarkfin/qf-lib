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

import abc
from itertools import count
from typing import List, Sequence, Optional, Dict, Tuple

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


class SimulatedExecutor(metaclass=abc.ABCMeta):
    def __init__(self, data_handler: DataHandler, monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer,
                 order_id_generator: count, commission_model: CommissionModel, slippage_model: Slippage,
                 frequency: Frequency):

        self._data_handler = data_handler
        self._data_provider = data_handler.data_provider
        self._frequency = frequency

        self._monitor = monitor
        self._portfolio = portfolio
        self._timer = timer
        self._order_id_generator = order_id_generator
        self._commission_model = commission_model
        self._slippage_model = slippage_model

        # mappings: order_id -> order
        self._awaiting_orders = {}  # type: Dict[int, Order]

    @abc.abstractmethod
    def assign_order_ids(self, orders: Sequence[Order]) -> List[int]:
        """
        Assign the orders ids
        """
        pass

    def accept_orders(self, orders: Sequence[Order]):
        for order in orders:
            self._awaiting_orders[order.id] = order

    def cancel_all_open_orders(self):
        """
        Cancels all open orders
        """
        self._awaiting_orders.clear()

    def cancel_order(self, order_id: int) -> Optional[Order]:
        """
        Cancel Order of given id (if it exists). Returns the cancelled Order or None if couldn't find the Order
        of given id.
        """
        cancelled_order = self._awaiting_orders.pop(order_id, None)
        return cancelled_order

    def get_open_orders(self) -> List[Order]:
        """
        Returns all open orders
        """
        return list(self._awaiting_orders.values())

    def execute_orders(self, market_open=False, market_close=False):
        """
        Converts Orders into Transactions. Preserves the dictionary of unexecuted Orders (order_id -> Order)
        """
        open_orders_list = self.get_open_orders()
        if not open_orders_list:
            return

        tickers = [order.ticker for order in open_orders_list]
        no_slippage_fill_prices_list, to_be_executed_orders, expired_orders_list = \
            self._get_orders_with_fill_prices_without_slippage(open_orders_list, tickers, market_open, market_close)

        if len(to_be_executed_orders) > 0:
            current_time = self._timer.now()
            fill_prices, fill_volumes = self._slippage_model.process_orders(current_time, to_be_executed_orders,
                                                                            no_slippage_fill_prices_list)

            for order, fill_price, fill_volume in zip(to_be_executed_orders, fill_prices, fill_volumes):
                if fill_volume != 0 and is_finite_number(fill_price):
                    self._execute_order(order, fill_price, fill_volume)
                    # Delete the executed orders from awaiting orders dictionary
                    del self._awaiting_orders[order.id]

            # If any orders have been executed - update the portfolio
            self._portfolio.update()

        # Delete all expired orders
        for expired_order_id in expired_orders_list:
            del self._awaiting_orders[expired_order_id]

    def _execute_order(self, order: Order, fill_price: float, fill_volume: int):
        """
        Simulates execution of a single Order by converting the Order into Transaction.
        """
        timestamp = self._timer.now()
        commission = self._commission_model.calculate_commission(fill_volume, fill_price)

        transaction = Transaction(timestamp, order.ticker, fill_volume, fill_price, commission)

        self._monitor.record_transaction(transaction)
        self._portfolio.transact_transaction(transaction)

    @abc.abstractmethod
    def _get_orders_with_fill_prices_without_slippage(self, open_orders_list: List[Order], tickers: List[Ticker],
                                                      market_open: bool, market_close: bool) \
            -> Tuple[List[float], List[Order], List[int]]:
        """ Function used by the execute_orders function, to compute the fill prices for the given orders.

        Parameters
        ----------
        open_orders_list
            list of open orders
        tickers
            mapped tickers corresponding to the orders

        Returns
        --------
        no_slippage_prices
            prices of the tickers without slippage
        to_be_executed_orders
            list of orders that can be executes (has price and is traded)
        expired_orders_list
            list of orders numbers that will expire and therefore should be deleted from awaiting orders

        """
        pass
