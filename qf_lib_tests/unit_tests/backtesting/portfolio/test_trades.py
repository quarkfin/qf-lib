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
from typing import List
from unittest.mock import Mock

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class TestTrades(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.contract = Contract('AAPL US Equity', security_type='STK', exchange='NYSE')
        cls.time = str_to_date('2020-01-01')

    def setUp(self):
        self.portfolio = Portfolio(Mock(), 100000, Mock(), Mock())

    @staticmethod
    def _cash_move(transaction):
        return -1 * transaction.price * transaction.quantity * transaction.contract.contract_size - transaction.commission

    def transact_transactions_and_check_portfolio_state_for_closed_position(self, transactions: List[Transaction]):
        """
        Transact all the given transactions.
        In the end, if the position is closed, check if the sum of pnl of the trades is equal to cash move.
        """
        position_size = 0

        for transaction in transactions:
            self.portfolio.transact_transaction(transaction)
            position_size += transaction.quantity

        cash_move = sum(self._cash_move(t) for t in transactions)

        if position_size == 0:
            # The position should be closed now
            self.assertEqual(len(self.portfolio.open_positions_dict), 0)
            # As the position is closed, the sum of trades pnl should be equal to cash move
            pnl_trades = sum([trade.pnl for trade in self.portfolio.trade_list()])

            self.assertAlmostEqual(pnl_trades, cash_move, places=6)
        else:
            position = self.portfolio.open_positions_dict[self.contract]
            pnl_trades = sum([trade.pnl for trade in self.portfolio.trade_list()]) + position.unrealised_pnl
            self.assertAlmostEqual(pnl_trades, cash_move, places=6)

    def test_trades_pnl_without_commission_closed_position_1(self):

        transactions = [
            Transaction(self.time, self.contract, quantity=800, price=120, commission=0.0),
            # Decreasing LONG position
            Transaction(self.time, self.contract, quantity=-200, price=124, commission=0.0),
            # Increasing existing LONG position
            Transaction(self.time, self.contract, quantity=400, price=132, commission=0.0),
            # Closing position
            Transaction(self.time, self.contract, quantity=-1000, price=140, commission=0.0)
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)

    def test_trades_pnl_without_commission_closed_position_2(self):
        """Create LONG position and issue only transactions, which decrease this position."""
        transactions = [
            Transaction(self.time, self.contract, quantity=800, price=120, commission=0.0),
            # Decreasing LONG position
            Transaction(self.time, self.contract, quantity=-100, price=124, commission=0.0),
            # Decreasing LONG position
            Transaction(self.time, self.contract, quantity=-400, price=132, commission=0.0),
            # Closing position
            Transaction(self.time, self.contract, quantity=-300, price=140, commission=0.0)
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)

    def test_trades_pnl_without_commsission_closed_position_4(self):
        """Create LONG position in the first 2 transactions, then decrease it to be smaller then the size after
        first transaction."""
        transactions = [
            Transaction(self.time, self.contract, 50, 100, 0),
            Transaction(self.time, self.contract, 30, 120, 0),
            Transaction(self.time, self.contract, -20, 175, 0),
            Transaction(self.time, self.contract, -30, 160, 0),
            Transaction(self.time, self.contract, 20, 180, 0),
            Transaction(self.time, self.contract, -70, 190, 0),
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)

    def test_trades_pnl_without_commsission_closed_position_5(self):
        transactions = [
            Transaction(self.time, self.contract, -50, 100, 0),
            Transaction(self.time, self.contract, -30, 120, 0),
            Transaction(self.time, self.contract, 20, 175, 0),
            Transaction(self.time, self.contract, 60, 160, 0),
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)

    def test_trades_pnl_without_commission_split_transactions_closed_position_1(self):
        """Force transactions splitting."""
        transactions = [
            Transaction(self.time, self.contract, quantity=200, price=120, commission=0.0),
            # Force the transaction splitting and creating a new position
            Transaction(self.time, self.contract, quantity=-500, price=124, commission=0.0),
            # Force another transaction splitting and creating a new position
            Transaction(self.time, self.contract, quantity=600, price=132, commission=0.0),
            # Close the position
            Transaction(self.time, self.contract, quantity=-300, price=140, commission=0.0)
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)

    def test_trades_pnl_without_commission_split_transactions_closed_position_2(self):
        transactions = [
            Transaction(self.time, self.contract, quantity=200, price=120, commission=0.0),
            # Force the transaction splitting and creating a new position
            Transaction(self.time, self.contract, quantity=-500, price=124, commission=0.0),
            # Increase the new position
            Transaction(self.time, self.contract, quantity=-300, price=132, commission=0.0),
            # Force position splitting
            Transaction(self.time, self.contract, quantity=700, price=140, commission=0.0),
            # Close the position
            Transaction(self.time, self.contract, quantity=-100, price=140, commission=0.0)
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)

    def test_trades_pnl_without_commission_split_transactions_open_position(self):
        transactions = [
            Transaction(self.time, self.contract, quantity=200, price=120, commission=0.0),
            Transaction(self.time, self.contract, quantity=-500, price=124, commission=0.0),
            Transaction(self.time, self.contract, quantity=-300, price=132, commission=0.0),
            Transaction(self.time, self.contract, quantity=700, price=140, commission=0.0),
            Transaction(self.time, self.contract, quantity=-500, price=124, commission=0.0),
            Transaction(self.time, self.contract, quantity=600, price=132, commission=0.0),
        ]

        self.transact_transactions_and_check_portfolio_state_for_closed_position(transactions)
