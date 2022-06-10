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
from qf_lib.backtesting.execution_handler.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_datetime import date_to_datetime
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class StopOrdersExecutor(SimulatedExecutor):
    def assign_order_ids(self, orders: Sequence[Order]) -> List[int]:
        tickers = [order.ticker for order in orders]

        unique_tickers_list = list(set(tickers))
        prices_at_acceptance_time = self._data_handler.get_last_available_price(unique_tickers_list)

        order_id_list = []
        for order, ticker in zip(orders, tickers):
            current_price = prices_at_acceptance_time[ticker]
            execution_style = order.execution_style  # type: StopOrder
            stop_price = execution_style.stop_price

            if order.quantity < 0:
                if stop_price >= current_price:
                    raise ValueError(
                        "Incorrect stop price ({stop_price:5.2f}). "
                        "For the Sell Stop it must be placed below "
                        "the current market price ({current_price:5.2f})".format(
                            stop_price=stop_price, current_price=current_price
                        ))
            elif order.quantity > 0:
                if stop_price <= current_price:
                    raise ValueError(
                        "Incorrect stop price ({stop_price:5.2f}). "
                        "For the Buy Stop it must be placed above "
                        "the current market price ({current_price:5.2f})".format(
                            stop_price=stop_price, current_price=current_price
                        ))
            else:
                raise ValueError("Incorrect order quantity (quantity: 0)")

            order_id = next(self._order_id_generator)
            order.id = order_id
            order_id_list.append(order_id)

        return order_id_list

    def _get_orders_with_fill_prices_without_slippage(self, open_orders_list, tickers, market_open, market_close):
        no_slippage_fill_prices_list = []
        to_be_executed_orders = []
        expired_stop_orders = []  # type: List[int]

        unique_tickers = list(set(tickers))
        # index=tickers, columns=fields
        current_bars_df = self._get_latest_available_bars(unique_tickers)  # type: QFDataFrame

        # Check at first if at this moment of time, expiry checks should be made or not (optimization reasons)
        if market_close:
            for order, ticker in zip(open_orders_list, tickers):
                current_bar = current_bars_df.loc[ticker, :]
                no_slippage_fill_price = self._calculate_no_slippage_fill_price(current_bar, order)

                if no_slippage_fill_price is not None:
                    to_be_executed_orders.append(order)
                    no_slippage_fill_prices_list.append(no_slippage_fill_price)
                else:
                    # the Order cannot be executed
                    if self._order_expires(order):
                        expired_stop_orders.append(order.id)
        else:
            for order, ticker in zip(open_orders_list, tickers):
                current_bar = current_bars_df.loc[ticker, :]
                no_slippage_fill_price = self._calculate_no_slippage_fill_price(current_bar, order)

                if no_slippage_fill_price is not None:
                    to_be_executed_orders.append(order)
                    no_slippage_fill_prices_list.append(no_slippage_fill_price)

        return no_slippage_fill_prices_list, to_be_executed_orders, expired_stop_orders

    def _get_latest_available_bars(self, tickers: Sequence[Ticker]) -> QFDataFrame:
        """
        Gets the latest available bars for given Tickers. The result is a QFDataFrame with Tickers as an index and
        PriceFields as columns.

        In case of daily trading, the bar without NaN values is returned only at the Market Close Event time, as the
        stop orders are executed only on the market close in that case.

        In case of intraday trading (for N minutes frequency) the latest bar can be returned in the time between
        MarketOpenEvent and the MarketCloseEvent.

        """
        if not tickers:
            return QFDataFrame(columns=PriceField.ohlcv())

        assert self._frequency >= Frequency.DAILY, "Lower than daily frequency is not supported by the simulated " \
                                                   "executor"
        current_datetime = self._timer.now()
        market_close_time = current_datetime + MarketCloseEvent.trigger_time() == current_datetime

        if self._frequency == Frequency.DAILY:
            # In case of daily trading we want the Stop Orders to be "executed" on the market close, so before that
            # no data should be returned
            if not market_close_time:
                return QFDataFrame(index=tickers, columns=PriceField.ohlcv())
            else:
                current_datetime = date_to_datetime(current_datetime.date())
                start_date = current_datetime
        else:
            # In case of intraday trading the current full bar is always indexed by the left side of the time range
            start_date = current_datetime - self._frequency.time_delta()

        return self._data_handler.get_price(tickers, PriceField.ohlcv(), start_date, start_date, self._frequency)

    def _calculate_no_slippage_fill_price(self, current_bar, order):
        """
        Returns the price which should be used for calculating the real fill price later on. It can return either:
        OPEN or stop price. If the market opens at the price which triggers StopOrders instantly, the OPEN price
        is returned. Otherwise if the LOW price (for Sell Stop) or HIGH price (for Buy Stop) exceeds the stop price,
        the stop price is returned. If none of the above conditions is met, None is returned (which means that
        StopOrder shouldn't be executed at any price).
        """
        # Make sure that at least all values except Volume are available. Volume is not available for currencies.
        price_bar = tuple(current_bar.loc[[PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]])
        if None in price_bar:
            return None

        open_price, high_price, low_price, close_price = price_bar

        stop_price = order.execution_style.stop_price
        is_sell_stop = order.quantity < 0
        no_slippage_fill_price = None

        if is_sell_stop:
            if open_price <= stop_price:
                no_slippage_fill_price = open_price
            else:
                if low_price <= stop_price:
                    no_slippage_fill_price = stop_price
        else:  # is buy stop
            if open_price >= stop_price:
                no_slippage_fill_price = open_price
            else:
                if high_price >= stop_price:
                    no_slippage_fill_price = stop_price

        return no_slippage_fill_price

    def _check_order_validity(self, order):
        assert order.time_in_force == TimeInForce.DAY or order.time_in_force == TimeInForce.GTC, \
            "Only TimeInForce.DAY or TimeInForce.GTC Time in Force is accepted by StopOrdersExecutor"
        assert isinstance(order.execution_style, StopOrder), \
            "Only StopOrder ExecutionStyle is supported by StopOrdersExecutor"

    @staticmethod
    def _order_expires(order: Order):
        """
        The orders for the standard market orders executor should not expiry.

        In case of on market close orders execution, the orders should expire if their TimeInForce is not equal to GTC.
        DAY orders will be dropped at this moment.
        """
        return order.time_in_force != TimeInForce.GTC
