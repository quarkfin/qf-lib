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

from qf_lib.backtesting.portfolio.backtest_crypto_position import BacktestCryptoPosition
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.tickers.tickers import BinanceTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestBacktestPosition(unittest.TestCase):
    """
    Tests for the BacktestPositionFactory.create_position class. For tests on PnL please see this website:
    https://www.tradingtechnologies.com/help/fix-adapter-reference/pl-calculation-algorithm/understanding-pl-calculations/
    """

    def setUp(self):
        self.ticker = DummyTicker('Example Stock')
        self.crypto_ticker = BinanceTicker('BTC', 'BUSD')
        self.start_time = str_to_date('2017-01-01')  # dummy time
        self.random_time = str_to_date('2017-02-02')  # dummy time
        self.end_time = str_to_date('2018-02-03')  # dummy time

    def test_creating_empty_position(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        self.assertEqual(position.ticker(), self.ticker)
        self.assertEqual(position._is_closed, False)
        self.assertEqual(position.quantity(), 0)
        self.assertEqual(position.current_price, 0)
        self.assertEqual(position.direction(), 0)
        self.assertEqual(position.start_time, None)

    def test_creating_empty_crypto_position(self):
        position = BacktestPositionFactory.create_position(self.crypto_ticker)
        self.assertEqual(position.ticker(), self.crypto_ticker)
        self.assertEqual(position._is_closed, False)
        self.assertEqual(position.quantity(), 0)
        self.assertEqual(position.current_price, 0)
        self.assertEqual(position.direction(), 0)
        self.assertEqual(position.start_time, None)
        self.assertTrue(isinstance(position, BacktestCryptoPosition))

    def test_transact_transaction_1(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        quantity = 50
        price = 100
        commission = 5

        transaction = Transaction(self.random_time, self.ticker, quantity, price, commission)

        position.transact_transaction(transaction)

        self.assertEqual(position.ticker(), self.ticker)
        self.assertEqual(position._is_closed, False)
        self.assertEqual(position.quantity(), quantity)
        self.assertEqual(position.current_price, 0)  # set by update_price
        self.assertEqual(position.direction(), 1)
        self.assertEqual(position.start_time, self.random_time)

    def test_crypto_transact_transaction_1(self):
        position = BacktestPositionFactory.create_position(self.crypto_ticker)
        quantity = 55.5
        price = 100
        commission = 5

        transaction = Transaction(self.random_time, self.crypto_ticker, quantity, price, commission)

        position.transact_transaction(transaction)

        self.assertEqual(position.ticker(), self.crypto_ticker)
        self.assertEqual(position._is_closed, False)
        self.assertEqual(position.quantity(), quantity)
        self.assertEqual(position.current_price, 0)  # set by update_price
        self.assertEqual(position.direction(), 1)
        self.assertEqual(position.start_time, self.random_time)

    def test_transact_transaction_2(self):
        position = BacktestPositionFactory.create_position(self.ticker)

        quantity1 = 50
        price1 = 100
        commission1 = 5
        transaction1 = Transaction(self.random_time, self.ticker, quantity1, price1, commission1)
        position.transact_transaction(transaction1)

        quantity2 = 30
        price2 = 120
        commission2 = 7
        transaction2 = Transaction(self.random_time, self.ticker, quantity2, price2, commission2)
        position.transact_transaction(transaction2)

        self.assertEqual(position.ticker(), self.ticker)
        self.assertEqual(position._is_closed, False)
        self.assertEqual(position.quantity(), quantity1 + quantity2)
        self.assertEqual(position.direction(), 1)
        self.assertEqual(position.start_time, self.random_time)
        self.assertEqual(position.current_price, 0)  # set by update_price

    def test_transact_transaction_3(self):
        position = BacktestPositionFactory.create_position(self.ticker)

        quantity1 = 50
        price1 = 100
        commission1 = 5
        position.transact_transaction(Transaction(self.random_time, self.ticker, quantity1, price1, commission1))

        quantity2 = 30
        price2 = 120
        commission2 = 7
        position.transact_transaction(Transaction(self.random_time, self.ticker, quantity2, price2, commission2))

        quantity3 = -40
        price3 = 150
        commission3 = 11
        transaction3 = Transaction(self.random_time, self.ticker, quantity3, price3, commission3)
        position.transact_transaction(transaction3)

        self.assertEqual(position.ticker(), self.ticker)
        self.assertEqual(position._is_closed, False)
        self.assertEqual(position.quantity(), quantity1 + quantity2 + quantity3)
        self.assertEqual(position.direction(), 1)
        self.assertEqual(position.start_time, self.random_time)

    def test_update_price(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        quantity = 50
        price = 100
        commission = 5
        position.transact_transaction(Transaction(self.random_time, self.ticker, quantity, price, commission))

        self.assertEqual(position.current_price, 0)  # set by update_price

        bid_price = 110
        position.update_price(bid_price=bid_price, ask_price=bid_price + 1)

        self.assertEqual(position.current_price, bid_price)

        bid_price = 120
        position.update_price(bid_price=bid_price, ask_price=bid_price + 1)
        self.assertEqual(position.current_price, bid_price)

    def test_without_commission_position(self):
        position = BacktestPositionFactory.create_position(self.ticker)

        transactions = [
            Transaction(self.start_time, self.ticker, 50, 100, 0),
            Transaction(self.start_time, self.ticker, 30, 120, 0),
            Transaction(self.start_time, self.ticker, -20, 175, 0),
            Transaction(self.start_time, self.ticker, -30, 160, 0),
            Transaction(self.start_time, self.ticker, 10, 150, 0),
            Transaction(self.start_time, self.ticker, 10, 170, 0),
            Transaction(self.start_time, self.ticker, -20, 150, 0)
        ]

        for transaction in transactions:
            position.transact_transaction(transaction)

        current_price = 110
        position.update_price(current_price, 120)

        self.assertEqual(position.ticker(), self.ticker)

        position_quantity = sum(t.quantity for t in transactions)
        self.assertEqual(position.quantity(), position_quantity)

        self.assertEqual(position.current_price, current_price)

    def test_position(self):
        position = BacktestPositionFactory.create_position(self.ticker)

        transactions = (
            Transaction(self.start_time, self.ticker, 50, 100, 5),
            Transaction(self.start_time, self.ticker, 30, 120, 3),
            Transaction(self.start_time, self.ticker, -20, 175, 2),
            Transaction(self.start_time, self.ticker, -30, 160, 1),
            Transaction(self.start_time, self.ticker, 10, 150, 7),
            Transaction(self.start_time, self.ticker, 10, 170, 4),
            Transaction(self.start_time, self.ticker, -20, 150, 5)
        )

        for transaction in transactions:
            position.transact_transaction(transaction)
        position.update_price(110, 120)

        self.assertEqual(position.ticker(), self.ticker)
        self.assertEqual(position.quantity(), 30)
        self.assertEqual(position.current_price, 110)

    def test_position_close(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        self.assertEqual(position._is_closed, False)
        position.transact_transaction(Transaction(self.start_time, self.ticker, 20, 100, 0))
        self.assertEqual(position._is_closed, False)
        position.transact_transaction(Transaction(self.start_time, self.ticker, -10, 120, 20))
        self.assertEqual(position._is_closed, False)
        position.transact_transaction(Transaction(self.start_time, self.ticker, -10, 110, 20))
        self.assertEqual(position._is_closed, True)

    def test_position_stats_on_close(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        position.transact_transaction(Transaction(self.start_time, self.ticker, 20, 100, 50))
        position.update_price(110, 120)

        closing_transaction = Transaction(self.start_time, self.ticker, -20, 120, 50)
        position.transact_transaction(closing_transaction)

        self.assertEqual(position.ticker(), self.ticker)
        self.assertEqual(position._is_closed, True)
        self.assertEqual(position.quantity(), 0)
        self.assertEqual(position.current_price, 110)  # set by update_price
        self.assertEqual(position.direction(), 1)
        self.assertEqual(position.start_time, self.start_time)

    def test_position_direction1(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        self.assertEqual(position.direction(), 0)
        position.transact_transaction(Transaction(self.start_time, self.ticker, 20, 100, 0))
        self.assertEqual(position.direction(), 1)
        position.transact_transaction(Transaction(self.start_time, self.ticker, -10, 100, 0))
        self.assertEqual(position.direction(), 1)
        position.transact_transaction(Transaction(self.start_time, self.ticker, -10, 100, 0))
        self.assertEqual(position.direction(), 1)

    def test_position_direction2(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        self.assertEqual(position.direction(), 0)

        position.transact_transaction(Transaction(self.start_time, self.ticker, 20, 100, 0))
        self.assertEqual(position.direction(), 1)

        with self.assertRaises(AssertionError):
            # position does not allow going directly short from long
            position.transact_transaction(Transaction(self.start_time, self.ticker, -30, 100, 0))

        position = BacktestPositionFactory.create_position(self.ticker)
        self.assertEqual(position.direction(), 0)

        position.transact_transaction(Transaction(self.start_time, self.ticker, -20, 100, 0))
        self.assertEqual(position.direction(), -1)

        with self.assertRaises(AssertionError):
            # position does not allow going directly short from long
            position.transact_transaction(Transaction(self.start_time, self.ticker, 30, 100, 0))

    def test_closed_position(self):
        position = BacktestPositionFactory.create_position(self.ticker)
        position.transact_transaction(Transaction(self.start_time, self.ticker, 20, 100, 0))
        position.transact_transaction(Transaction(self.start_time, self.ticker, -20, 100, 0))

        with self.assertRaises(AssertionError):
            # position is now closed and should not accept new transactions
            position.transact_transaction(Transaction(self.start_time, self.ticker, 1, 100, 0))

        with self.assertRaises(AssertionError):
            # position is now closed and should not accept new transactions
            position.transact_transaction(Transaction(self.start_time, self.ticker, -1, 100, 0))

        with self.assertRaises(AssertionError):
            # position is now closed
            position.update_price(110, 120)


if __name__ == "__main__":
    unittest.main()
