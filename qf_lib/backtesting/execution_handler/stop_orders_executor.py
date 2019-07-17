from itertools import count
from typing import List, Sequence

import pandas as pd

from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.timer import Timer


class StopOrdersExecutor(SimulatedExecutor):

    def __init__(self, contracts_to_tickers_mapper: ContractTickerMapper, data_handler: DataHandler,
                 monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer, order_id_generator: count,
                 commission_model: CommissionModel, slippage_model: Slippage):

        super().__init__(contracts_to_tickers_mapper, data_handler, monitor, portfolio, timer,
                         order_id_generator, commission_model, slippage_model)

    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        tickers = [self._contracts_to_tickers_mapper.contract_to_ticker(order.contract) for order in orders]

        unique_tickers_list = list(set(tickers))
        prices_at_acceptance_time = self._data_handler.get_last_available_price(unique_tickers_list)

        order_id_list = []
        for order, ticker in zip(orders, tickers):
            current_price = prices_at_acceptance_time[ticker]
            execution_style = order.execution_style  # type: StopOrder
            stop_price = execution_style.stop_price

            order_id = next(self._order_id_generator)

            if order.quantity < 0:
                if stop_price < current_price:
                    self._awaiting_orders[order_id] = order
                else:
                    raise ValueError(
                        "Incorrect stop price ({stop_price:5.2f}). "
                        "For the Sell Stop it must be placed below "
                        "the current market price ({current_price:5.2f})".format(
                            stop_price=stop_price, current_price=current_price
                        ))
            elif order.quantity > 0:
                if stop_price > current_price:
                    self._awaiting_orders[order_id] = order
                else:
                    raise ValueError(
                        "Incorrect stop price ({stop_price:5.2f}). "
                        "For the Buy Stop it must be placed above "
                        "the current market price ({current_price:5.2f})".format(
                            stop_price=stop_price, current_price=current_price
                        ))
            else:
                raise ValueError("Incorrect order quantity (quantity: 0)")

            order.id = order_id
            order_id_list.append(order_id)

        return order_id_list

    def _get_orders_with_fill_prices_without_slippage(self, open_orders_list, tickers):
        no_slippage_fill_prices_list = []
        to_be_executed_orders = []
        unexecuted_stop_orders_data_dict = {}

        unique_tickers = list(set(tickers))
        # index=tickers, columns=fields
        current_bars_df = self._data_handler.get_bar_for_today(unique_tickers)  # type: pd.DataFrame

        for order, ticker in zip(open_orders_list, tickers):
            current_bar = current_bars_df.loc[ticker, :]
            no_slippage_fill_price = self._calculate_no_slippage_fill_price(current_bar, order)

            if no_slippage_fill_price is None:  # the Order cannot be executed
                if order.time_in_force == TimeInForce.GTC:
                    # preserve only GTC orders. DAY orders will be dropped at this point
                    unexecuted_stop_orders_data_dict[order.id] = order
            else:
                to_be_executed_orders.append(order)
                no_slippage_fill_prices_list.append(no_slippage_fill_price)

        return no_slippage_fill_prices_list, to_be_executed_orders, unexecuted_stop_orders_data_dict

    def _calculate_no_slippage_fill_price(self, current_bar, order):
        """
        Returns the price which should be used for calculating the real fill price later on. It can return either:
        OPEN or stop price. If the market opens at the price which triggers StopOrders instantly, the OPEN price
        is returned. Otherwise if the LOW price (for Sell Stop) or HIGH price (for Buy Stop) exceeds the stop price,
        the stop price is returned. If none of the above conditions is met, None is returned (which means that
        StopOrder shouldn't be executed at any price).
        """
        # Make sure that at least all values except Volume are available. Volume is not available for currencies.
        price_bar = current_bar.loc[[PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]]
        if price_bar.isnull().values.any():  # there is no data for today for a given Ticker; skip it
            return None

        stop_price = order.execution_style.stop_price
        open_price = current_bar.loc[PriceField.Open]
        is_sell_stop = order.quantity < 0
        no_slippage_fill_price = None

        if is_sell_stop:
            if open_price <= stop_price:
                no_slippage_fill_price = open_price
            else:
                low_price = current_bar[PriceField.Low]
                if low_price <= stop_price:
                    no_slippage_fill_price = stop_price
        else:  # is buy stop
            if open_price >= stop_price:
                no_slippage_fill_price = open_price
            else:
                high_price = current_bar[PriceField.High]
                if high_price >= stop_price:
                    no_slippage_fill_price = stop_price

        return no_slippage_fill_price

    def _check_order_validity(self, order):
        assert order.time_in_force == TimeInForce.DAY or order.time_in_force == TimeInForce.GTC, \
            "Only TimeInForce.DAY or TimeInForce.GTC Time in Force is accepted by StopOrdersExecutor"
        assert isinstance(order.execution_style, StopOrder), \
            "Only StopOrder ExecutionStyle is supported by StopOrdersExecutor"
