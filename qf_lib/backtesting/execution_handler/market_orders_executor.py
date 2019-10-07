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

from itertools import count
from typing import List, Sequence

from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


class MarketOrdersExecutor(SimulatedExecutor):
    def __init__(self, contracts_to_tickers_mapper: ContractTickerMapper, data_handler: DataHandler,
                 monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer, order_id_generator: count,
                 commission_model: CommissionModel, slippage_model: Slippage):

        super().__init__(contracts_to_tickers_mapper, data_handler, monitor, portfolio, timer,
                         order_id_generator, commission_model, slippage_model)

    def assign_order_ids(self, orders: Sequence[Order]) -> List[int]:
        order_id_list = []
        for order in orders:
            self._check_order_validity(order)

            order.id = next(self._order_id_generator)
            order_id_list.append(order.id)

        return order_id_list

    def _get_orders_with_fill_prices_without_slippage(self, market_orders_list, tickers, market_open, market_close):
        unique_tickers = list(set(tickers))
        current_prices_series = self._data_handler.get_current_price(unique_tickers)

        expired_orders = []  # type: List[int]
        to_be_executed_orders = []
        no_slippage_prices = []

        # Check at first if at this moment of time, expiry checks should be made or not (optimization reasons)
        if market_open or market_close:
            # In case of market open or market close, some of the orders may expire
            for order, ticker in zip(market_orders_list, tickers):
                security_price = current_prices_series[ticker]

                if is_finite_number(security_price):
                    to_be_executed_orders.append(order)
                    no_slippage_prices.append(security_price)
                elif self._order_expires(order, market_open, market_close):
                    expired_orders.append(order.id)
        else:
            for order, ticker in zip(market_orders_list, tickers):
                security_price = current_prices_series[ticker]

                if is_finite_number(security_price):
                    to_be_executed_orders.append(order)
                    no_slippage_prices.append(security_price)

        return no_slippage_prices, to_be_executed_orders, expired_orders

    def _check_order_validity(self, order):
        assert order.execution_style == MarketOrder(), \
            "Only MarketOrder ExecutionStyle is supported by MarketOrdersExecutor"

    @staticmethod
    def _order_expires(order: Order, market_open: bool, market_close: bool):
        """
        The orders for the standard market orders executor should not expiry.

        In case of on market close orders execution, the orders should expire if their TimeInForce is not equal to GTC.
        DAY orders will be dropped at this moment.

        In case of market open orders execution, the orders should expiry if their TimeInForce is equal to OPG.
        """
        if market_open and order.time_in_force == TimeInForce.OPG:
            return True
        elif market_close and order.time_in_force != TimeInForce.GTC:
            return True
        else:
            return False
