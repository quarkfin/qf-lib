import logging
from typing import Dict, List, Sequence, Tuple, Optional

import pandas as pd

from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer


class MarketOnCloseOrdersExecutor(SimulatedExecutor):

    def __init__(self, contracts_to_tickers_mapper: ContractTickerMapper, data_handler: DataHandler,
                 monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer, order_id_generator,
                 commission_model: CommissionModel, slippage_model: Slippage):

        super().__init__(contracts_to_tickers_mapper, data_handler, monitor, portfolio, timer, order_id_generator,
                         commission_model, slippage_model)

        self._logger = logging.getLogger(self.__class__.__name__)

    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        order_id_list = []
        for order in orders:
            order.id = next(self._order_id_generator)

            order_id_list.append(order.id)
            self._awaiting_orders[order.id] = order

        return order_id_list

    def cancel_order(self, order_id: int) -> Optional[Order]:
        """
        Cancel Order of given id (if it exists). Returns the cancelled Order or None if couldn't find the Order
        of given id.
        """
        cancelled_order = self._awaiting_orders.pop(order_id, None)
        return cancelled_order

    def cancel_all_open_orders(self):
        self._awaiting_orders.clear()

    def get_open_orders(self) -> List[Order]:
        return list(self._awaiting_orders.values())

    def execute_orders(self):
        """
        Converts Orders into Transactions. Returns dictionary of unexecuted Orders (order_id -> Order)
        """
        if not self._awaiting_orders:
            return

        open_orders_data = self._stop_orders_data_dict.values()
        tickers = [ticker for _, ticker in open_orders_data]

        no_slippage_fill_prices_list, to_be_executed_orders, unexecuted_stop_orders_data_dict = \
            self._get_orders_with_fill_prices_without_slippage(open_orders_data, tickers)

        fill_prices, fill_volumes = self._slippage_model.apply_slippage(
            to_be_executed_orders, no_slippage_fill_prices_list
        )

        for order, fill_price in zip(to_be_executed_orders, fill_prices):
            self._execute_order(order, fill_price)

        self._stop_orders_data_dict = unexecuted_stop_orders_data_dict

    def _get_orders_with_fill_prices_without_slippage(self, open_orders_data, tickers):
        no_slippage_fill_prices_list = []
        to_be_executed_orders = []
        unexecuted_stop_orders_data_dict = {}

        unique_tickers = list(set(tickers))
        current_bars_df = self._data_handler.get_bar_for_today(
            unique_tickers
        )  # type: pd.DataFrame  # index=tickers, columns=fields

        for order, ticker in open_orders_data:
            current_bar = current_bars_df.loc[ticker, :]
            no_slippage_fill_price = self._calculate_no_slippage_fill_price(current_bar, order)

            if no_slippage_fill_price is None:  # the Order cannot be executed
                unexecuted_stop_orders_data_dict[order.id] = (order, ticker)
            else:
                to_be_executed_orders.append(order)
                no_slippage_fill_prices_list.append(no_slippage_fill_price)

        return no_slippage_fill_prices_list, to_be_executed_orders, unexecuted_stop_orders_data_dict

