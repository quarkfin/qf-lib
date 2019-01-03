import abc
from typing import List, Sequence, Optional

from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.dateutils.timer import Timer


class SimulatedExecutor(metaclass=abc.ABCMeta):
    def __init__(self, contracts_to_tickers_mapper: ContractTickerMapper, data_handler: DataHandler,
                 monitor: AbstractMonitor, portfolio: Portfolio, timer: Timer,
                 order_id_generator, commission_model: CommissionModel, slippage_model: Slippage):
        self._contracts_to_tickers_mapper = contracts_to_tickers_mapper
        self._data_handler = data_handler
        self._monitor = monitor
        self._portfolio = portfolio
        self._timer = timer
        self._order_id_generator = order_id_generator
        self._commission_model = commission_model
        self._slippage_model = slippage_model

    @abc.abstractmethod
    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        pass

    @abc.abstractmethod
    def cancel_order(self, order_id: int) -> Optional[Order]:
        pass

    @abc.abstractmethod
    def cancel_all_open_orders(self):
        pass

    @abc.abstractmethod
    def get_open_orders(self) -> List[Order]:
        pass

    @abc.abstractmethod
    def execute_orders(self):
        pass

    def _execute_order(self, order: Order, fill_price: float):
        """
        Simulates execution of a single Order by converting the Order into Transaction.
        """
        timestamp = self._timer.now()
        contract = order.contract
        quantity = order.quantity

        commission = self._commission_model.calculate_commission(order, fill_price)

        transaction = Transaction(timestamp, contract, quantity, fill_price, commission)

        self._monitor.record_transaction(transaction)
        self._portfolio.transact_transaction(transaction)

