import logging
import math
from typing import Dict, List, Sequence, Optional

from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.dateutils.timer import Timer


class MarketOrdersExecutor(object):
    def __init__(self, contracts_to_tickers_mapper: ContractTickerMapper, data_handler: DataHandler,
                 commission_model: CommissionModel, monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer,
                 order_id_generator, slippage_model: Slippage):
        self._contracts_to_tickers_mapper = contracts_to_tickers_mapper
        self._data_handler = data_handler
        self._commission_model = commission_model
        self._monitor = monitor
        self._portfolio = portfolio
        self._timer = timer
        self._order_id_generator = order_id_generator
        self._slippage_model = slippage_model

        self._awaiting_orders = {}  # type: Dict[int, Order]  # order_id -> Order

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
        market_orders_list = self.get_open_orders()
        if not market_orders_list:
            return

        tickers = [self._contracts_to_tickers_mapper.contract_to_ticker(order.contract) for order in market_orders_list]

        no_slippage_prices, to_be_executed_orders, unexecuted_orders_dict = \
            self._get_orders_with_fill_prices_without_slippage(market_orders_list, tickers)

        fill_prices, fill_volumes = self._slippage_model.apply_slippage(to_be_executed_orders, no_slippage_prices)

        for order, fill_price in zip(to_be_executed_orders, fill_prices):
            self._execute_order(order, fill_price)

        self._awaiting_orders = unexecuted_orders_dict

    def _get_orders_with_fill_prices_without_slippage(self, market_orders_list, tickers):
        unique_tickers = list(set(tickers))
        current_prices_series = self._data_handler.get_current_price(unique_tickers)

        unexecuted_orders_dict = {}  # type: Dict[int, Order]
        to_be_executed_orders = []
        no_slippage_prices = []

        for order, ticker in zip(market_orders_list, tickers):
            security_price = current_prices_series[ticker]

            if math.isnan(security_price):
                unexecuted_orders_dict[order.id] = order
            else:
                to_be_executed_orders.append(order)
                no_slippage_prices.append(security_price)

        return no_slippage_prices, to_be_executed_orders, unexecuted_orders_dict

    def _execute_order(self, order: Order, security_price: float):
        """
        Simulates execution of a single Order by converting the Order into Transaction.
        """
        timestamp = self._timer.now()
        contract = order.contract
        quantity = order.quantity

        fill_price = self._calculate_fill_price(order, security_price)
        commission = self._commission_model.calculate_commission(order, fill_price)

        transaction = Transaction(timestamp, contract, quantity, fill_price, commission)
        self._monitor.record_transaction(transaction)
        self._portfolio.transact_transaction(transaction)

        self._logger.info("Order executed. Transaction has been created:\n{:s}".format(str(transaction)))

    @classmethod
    def _calculate_fill_price(cls, _: Order, security_price: float) -> float:
        """
        Dummy fill price calculation. Take the market price
        """
        return security_price
