import logging
import math
from itertools import chain
from typing import Dict, List, Sequence, Tuple, Optional

import pandas as pd

from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated.order_states import OrderState
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer


class StopOrdersExecutor(object):

    def __init__(self, contracts_to_tickers_mapper: ContractTickerMapper, data_handler: DataHandler, order_id_generator,
                 commission_model: CommissionModel, monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer):
        self._contracts_to_tickers_mapper = contracts_to_tickers_mapper
        self._data_handler = data_handler
        self._order_id_generator = order_id_generator
        self._timer = timer
        self._commission_model = commission_model
        self._monitor = monitor
        self._portfolio = portfolio

        # mappings: order_id -> (order, ticker, price_when_order_accepted)
        self._buy_stop_orders_data = {}  # type: Dict[int, Tuple[Order, Ticker]
        self._sell_stop_orders_data = {}  # type: Dict[int, Tuple[Order, Ticker]

        self._logger = logging.getLogger(self.__class__.__name__)

    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        # order, ticker, price_when_accepted
        tickers = [
            self._contracts_to_tickers_mapper.contract_to_ticker(order.contract) for order in orders
        ]

        prices_at_acceptance_time = self._data_handler.get_last_available_price(tickers)

        order_id_list = []
        for order, ticker, current_price in zip(orders, tickers, list(prices_at_acceptance_time.values)):
            execution_style = order.execution_style  # type: StopOrder
            stop_price = execution_style.stop_price

            order_id = next(self._order_id_generator)

            if order.quantity < 0:
                if stop_price < current_price:
                    self._sell_stop_orders_data[order_id] = (order, ticker)
                else:
                    raise ValueError(
                        "Incorrect stop price ({stop_price:5.2f}). "
                        "For the Sell Stop it must be placed below "
                        "the current market price ({{current_price:5.2f}})".format(
                            stop_price=stop_price, current_price=current_price
                        ))
            else:
                if stop_price > current_price:
                    self._buy_stop_orders_data[order_id] = (order, ticker)
                else:
                    raise ValueError(
                        "Incorrect stop price ({stop_price:5.2f}). "
                        "For the Sell Stop it must be placed below "
                        "the current market price ({{current_price:5.2f}})".format(
                            stop_price=stop_price, current_price=current_price
                        ))

            order.id = self._get_next_order_id()
            order.order_state = OrderState.AWAITING
            order_id_list.append(order_id)

        return order_id_list

    def cancel_all_open_orders(self):
        self._buy_stop_orders_data.clear()
        self._sell_stop_orders_data.clear()

    def cancel_order(self, order_id: int) -> Optional[Order]:
        cancelled_order, _ = self._buy_stop_orders_data.pop(order_id, (None, None))
        if cancelled_order is not None:
            return cancelled_order

        cancelled_order, _ = self._sell_stop_orders_data.pop(order_id, (None, None))
        if cancelled_order is not None:
            return cancelled_order

        return None

    def get_open_orders(self) -> List[Order]:
        all_open_orders_data = chain(self._buy_stop_orders_data.values(), self._sell_stop_orders_data.values())
        open_orders = [order for order, _ in all_open_orders_data]
        
        return open_orders

    def execute_orders(self):
        """
        Converts Orders into Transactions. Returns dictionary of unexecuted Orders (order_id -> Order)
        """
        if not self._buy_stop_orders_data and not self._sell_stop_orders_data:
            return

        all_open_orders_data = chain(self._buy_stop_orders_data.values(), self._sell_stop_orders_data.values())
        tickers = [ticker for _, ticker in all_open_orders_data]

        current_bars_df = self._data_handler.get_bar_for_today(tickers)  # type: pd.DataFrame  # [tickers, fields]

        unexecuted_sell_stop_orders_data_dict = {}
        unexecuted_buy_stop_orders_data_dict = {}

        for order, ticker in self._sell_stop_orders_data:
            low_price = current_bars_df.loc[ticker, PriceField.Low]
            stop_price = order.execution_style.stop_price

            if not math.isnan(low_price) and low_price < stop_price:
                self._execute_order(order)
            else:
                unexecuted_sell_stop_orders_data_dict[order.id] = (order, ticker)

        for order, ticker in self._buy_stop_orders_data:
            high_price = current_bars_df.loc[ticker, PriceField.High]
            stop_price = order.execution_style.stop_price

            if not math.isnan(high_price) and high_price > stop_price:
                self._execute_order(order)
            else:
                unexecuted_buy_stop_orders_data_dict[order.id] = (order, ticker)

        self._sell_stop_orders_data = unexecuted_sell_stop_orders_data_dict
        self._buy_stop_orders_data = unexecuted_buy_stop_orders_data_dict

    def _execute_order(self, order: Order):
        """
        Simulates execution of a single Order by converting the Order into Transaction.
        """
        timestamp = self._timer.now()
        contract = order.contract
        quantity = order.quantity

        fill_price = self._calculate_fill_price(order, order.execution_style.stop_price)

        commission = self._commission_model.calculate_commission(quantity, fill_price)

        transaction = Transaction(timestamp, contract, quantity, fill_price, commission)
        self._monitor.record_trade(transaction)

        self._logger.info("Order executed. Transaction has been created:\n{:s}".format(str(transaction)))
        self._portfolio.transact_transaction(transaction)

    def _calculate_fill_price(self, _, security_price):
        return security_price