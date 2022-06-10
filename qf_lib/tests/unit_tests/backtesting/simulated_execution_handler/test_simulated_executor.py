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
import unittest
from itertools import count
from unittest.mock import MagicMock, patch

from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.execution_handler.market_orders_executor import MarketOrdersExecutor
from qf_lib.backtesting.execution_handler.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import Timer


class TestSimulatedExecutor(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.example_ticker = BloombergTicker("Example Index")
        cls.example_ticker_2 = BloombergTicker("Example2 Index")
        cls.orders = [
            Order(ticker=cls.example_ticker,
                  quantity=1000,
                  execution_style=MarketOrder(),
                  time_in_force=TimeInForce.GTC),
            Order(ticker=cls.example_ticker_2,
                  quantity=1000,
                  execution_style=MarketOrder(),
                  time_in_force=TimeInForce.GTC),
        ]
        cls.backtest_date = str_to_date("2020-01-01")

    def setUp(self) -> None:
        def set_all_orders_to_be_executed(open_orders_list, tickers, market_open, market_close):
            """Assign to each open order price equal to mocked_price. Set all orders to be executed."""
            no_slippage_fill_prices_list = [100.00 for _ in open_orders_list]
            to_be_executed_orders = open_orders_list
            expired_orders_list = []
            return no_slippage_fill_prices_list, to_be_executed_orders, expired_orders_list

        self.patcher = patch.object(MarketOrdersExecutor, '_get_orders_with_fill_prices_without_slippage',
                                    side_effect=set_all_orders_to_be_executed)
        self.patcher.start()

        # List of transactions performed during a test
        self.recorded_transactions = []

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_accept_orders(self):
        simulated_executor = self._set_up_simulated_executor()
        simulated_executor.assign_order_ids(self.orders)
        simulated_executor.accept_orders(self.orders)

        self.assertCountEqual(simulated_executor.get_open_orders(), self.orders)

    def test_cancel_order(self):
        simulated_executor = self._set_up_simulated_executor()
        simulated_executor.assign_order_ids(self.orders)
        simulated_executor.accept_orders(self.orders)

        removed_order = self.orders[0]
        orders = [order for order in self.orders if order != removed_order]
        order = simulated_executor.cancel_order(removed_order.id)

        self.assertCountEqual(simulated_executor.get_open_orders(), orders)
        self.assertEqual(removed_order, order)

    def test_cancel_all_open_orders(self):
        simulated_executor = self._set_up_simulated_executor()
        simulated_executor.assign_order_ids(self.orders)
        simulated_executor.accept_orders(self.orders)

        simulated_executor.cancel_all_open_orders()
        self.assertCountEqual(simulated_executor.get_open_orders(), [])

    def test_execute_orders(self):
        mocked_fill_volume = 30
        mocked_fill_price = 100.0

        simulated_executor = self._set_up_simulated_executor(mocked_fill_price=mocked_fill_price,
                                                             mocked_fill_volume=mocked_fill_volume)
        simulated_executor.execute_orders()

        # No open orders were available, thus the list of transactions should be empty
        self.assertCountEqual(self.recorded_transactions, [])

        simulated_executor.assign_order_ids(self.orders)
        simulated_executor.accept_orders(self.orders)
        simulated_executor.execute_orders()

        # Both open orders were available
        expected_transactions = [Transaction(self.backtest_date,
                                             self.example_ticker,
                                             mocked_fill_volume, mocked_fill_price, 0.0),
                                 Transaction(self.backtest_date,
                                             self.example_ticker_2,
                                             mocked_fill_volume, mocked_fill_price, 0.0),
                                 ]
        self.assertCountEqual(self.recorded_transactions, expected_transactions)

    def test_execute_orders_with_zero_quantity(self):
        simulated_executor = self._set_up_simulated_executor(mocked_fill_volume=0)
        simulated_executor.assign_order_ids(self.orders)
        simulated_executor.accept_orders(self.orders)
        simulated_executor.execute_orders()

        # No transactions should be recorded
        self.assertCountEqual(self.recorded_transactions, [])

    def _set_up_simulated_executor(self, mocked_fill_price: float = 50.0, mocked_fill_volume: int = 50) -> \
            SimulatedExecutor:
        """Generates a customized mock of SimulatedExecutor."""

        def mock_apply_slippage(current_time, to_be_executed_orders, no_slippage_fill_prices_list):
            fill_prices = [mocked_fill_price for _ in to_be_executed_orders]
            fill_volumes = [mocked_fill_volume for _ in to_be_executed_orders]
            return fill_prices, fill_volumes

        slippage_model = MagicMock()
        slippage_model.process_orders.side_effect = mock_apply_slippage

        def mock_calculate_commission(fill_quantity, fill_price):
            return 0.0

        commission_model: CommissionModel = MagicMock()
        commission_model.calculate_commission.side_effect = mock_calculate_commission

        def mock_record_transaction(transaction: Transaction):
            self.recorded_transactions.append(transaction)

        monitor: AbstractMonitor = MagicMock()
        monitor.record_transaction.side_effect = mock_record_transaction

        timer: Timer = MagicMock()
        timer.now.return_value = self.backtest_date

        order_id_generator = count(start=1)
        simulated_executor = MarketOrdersExecutor(MagicMock(), monitor, MagicMock(), timer, order_id_generator,
                                                  commission_model, slippage_model, Frequency.DAILY)
        return simulated_executor
