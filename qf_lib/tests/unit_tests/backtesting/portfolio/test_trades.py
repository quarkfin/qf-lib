#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the 'License');
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an 'AS IS' BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import unittest
from unittest.mock import Mock

from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestTrades(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ticker = DummyTicker('AAPL US Equity', SecurityType.STOCK, 1)
        cls.start_time = str_to_date('2019-01-01')
        cls.time = str_to_date('2020-01-01')

    def setUp(self):
        self.portfolio = Portfolio(Mock(), 100000, Mock())
        self.trades_generator = TradesGenerator()

    def test_long_trade(self):
        transactions = [
            Transaction(self.start_time, self.ticker, 5, 10.0, 3.0),
            Transaction(self.time, self.ticker, 5, 11.0, 4.0),
            Transaction(self.time, self.ticker, -1, 13.0, 5.0),
            Transaction(self.time, self.ticker, 1, 14.0, 5.0),
            Transaction(self.time, self.ticker, -4, 15.0, 2.0),
            Transaction(self.time, self.ticker, -6, 16.0, 1.0),
        ]

        for t in transactions:
            self.portfolio.transact_transaction(t)

        # The position should be closed after executing all transactions
        self.assertCountEqual(self.portfolio.open_positions_dict, {})

        all_closed_positions_for_contract = [p for p in self.portfolio.closed_positions()
                                             if p.ticker() == self.ticker]
        self.assertEqual(len(all_closed_positions_for_contract), 1)
        position = all_closed_positions_for_contract[0]  # type: BacktestPosition

        trade_1 = self.trades_generator.create_trades_from_backtest_positions(position)
        trade_2 = self.trades_generator.create_trades_from_transactions(transactions)[0]
        commission = sum(t.commission for t in transactions)

        self.assertEqual(trade_1, trade_2)

        self.assertEqual(trade_1.commission, commission)
        self.assertEqual(trade_1.pnl, 50.0 - commission)
        self.assertEqual(trade_1.direction, 1.0)
        self.assertEqual(trade_1.start_time, self.start_time)
        self.assertEqual(trade_1.end_time, self.time)

    def test_short_trade(self):
        transactions = [
            Transaction(self.start_time, self.ticker, -5, 10.0, 3.0),
            Transaction(self.time, self.ticker, 1, 11.0, 4.0),
            Transaction(self.time, self.ticker, -9, 10.0, 5.0),
            Transaction(self.time, self.ticker, 4, 14.0, 5.0),
            Transaction(self.time, self.ticker, 8, 10.0, 2.0),
            Transaction(self.time, self.ticker, 1, 9.0, 1.0),
        ]

        for t in transactions:
            self.portfolio.transact_transaction(t)

        # The position should be closed after executing all transactions
        self.assertCountEqual(self.portfolio.open_positions_dict, {})

        all_closed_positions_for_contract = [p for p in self.portfolio.closed_positions()
                                             if p.ticker() == self.ticker]
        self.assertEqual(len(all_closed_positions_for_contract), 1)
        position = all_closed_positions_for_contract[0]

        trade_1 = self.trades_generator.create_trades_from_backtest_positions(position)
        trade_2 = self.trades_generator.create_trades_from_transactions(transactions)[0]
        commission = sum(t.commission for t in transactions)

        self.assertEqual(trade_1, trade_2)

        self.assertEqual(trade_1.commission, commission)
        self.assertEqual(trade_1.pnl, -16.0 - commission)
        self.assertEqual(trade_1.direction, -1.0)
        self.assertEqual(trade_1.start_time, self.start_time)
        self.assertEqual(trade_1.end_time, self.time)
