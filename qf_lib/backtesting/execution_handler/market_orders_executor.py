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

from typing import List, Sequence

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.execution_handler.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_datetime import date_to_datetime
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.series.qf_series import QFSeries


class MarketOrdersExecutor(SimulatedExecutor):
    def assign_order_ids(self, orders: Sequence[Order]) -> List[int]:
        order_id_list = []
        for order in orders:
            self._check_order_validity(order)

            order.id = next(self._order_id_generator)
            order_id_list.append(order.id)

        return order_id_list

    def _get_orders_with_fill_prices_without_slippage(self, market_orders_list, tickers, market_open, market_close):
        unique_tickers = list(set(tickers))
        current_prices_series = self._get_current_prices(unique_tickers)

        expired_orders = []  # type: List[int]
        to_be_executed_orders = []
        no_slippage_prices = []

        # Check at first if at this moment of time, expiry checks should be made or not (optimization reasons)
        if market_open or market_close:
            # In case of market open or market close, some of the orders may expire
            for order, ticker in zip(market_orders_list, tickers):
                security_price = current_prices_series.loc[ticker]

                if is_finite_number(security_price):
                    to_be_executed_orders.append(order)
                    no_slippage_prices.append(security_price)
                elif self._order_expires(order, market_open, market_close):
                    expired_orders.append(order.id)
        else:
            for order, ticker in zip(market_orders_list, tickers):
                security_price = current_prices_series.loc[ticker]

                if is_finite_number(security_price):
                    to_be_executed_orders.append(order)
                    no_slippage_prices.append(security_price)

        return no_slippage_prices, to_be_executed_orders, expired_orders

    def _get_current_prices(self, tickers: Sequence[Ticker]):
        """
        Function used to obtain the current prices for the tickers in order to further calculate fill prices for orders.
        The function uses data provider and not data handler, as it is necessary to get the current bar at each point
        in time to compute the fill prices.
        """
        if not tickers:
            return QFSeries()

        assert self._frequency >= Frequency.DAILY, "Lower than daily frequency is not supported by the simulated" \
                                                   " executor"

        # Compute the time ranges, used further by the get_price function
        current_datetime = self._timer.now()

        market_close_time = current_datetime + MarketCloseEvent.trigger_time() == current_datetime
        market_open_time = current_datetime + MarketOpenEvent.trigger_time() == current_datetime

        # In case of daily frequency, current price may be returned only at the Market Open or Market Close time
        if self._frequency == Frequency.DAILY and not (market_open_time or market_close_time):
            return QFSeries(index=tickers)

        if self._frequency == Frequency.DAILY:
            # Remove the time part from the datetime in case of daily frequency
            current_datetime = date_to_datetime(current_datetime.date())
            start_time_range = current_datetime
        elif market_close_time:
            # At the market close, in order to get the current price we need to take a bar that ends at the current time
            # and use the close price value
            start_time_range = current_datetime - self._frequency.time_delta()
        else:
            # At any other time during the day, in order to get the current price we need to take the bar that starts at
            # the current time and use the open price value
            start_time_range = current_datetime

        price_field = PriceField.Close if market_close_time else PriceField.Open
        prices = self._data_provider.get_price(tickers, price_field, start_time_range, start_time_range, self._frequency)
        return prices

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
