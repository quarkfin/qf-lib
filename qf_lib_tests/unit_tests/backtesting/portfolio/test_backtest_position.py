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

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class DummyPosition(BacktestPosition):
    def market_value(self) -> float:
        return None

    def total_exposure(self) -> float:
        return None

    def _cash_to_buy_or_proceeds_from_sale(self, transaction: Transaction) -> float:
        return None


class TestBacktestPosition(unittest.TestCase):
    """
    Tests for the BacktestPosition class. For tests on PnL please see this website:
    https://www.tradingtechnologies.com/help/fix-adapter-reference/pl-calculation-algorithm/understanding-pl-calculations/
    """

    def setUp(self):
        self.contract = Contract('AAPL US Equity', security_type='STK', exchange='NYSE')
        self.start_time = str_to_date('2017-01-01')  # dummy time
        self.random_time = str_to_date('2017-02-02')  # dummy time
        self.end_time = str_to_date('2018-02-03')  # dummy time

    def test_creating_empty_position(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.is_closed, False)
        self.assertEqual(position.quantity(), 0)
        self.assertEqual(position.current_price, 0)
        self.assertEqual(position.direction, 0)
        self.assertEqual(position.start_time, self.start_time)
        self.assertEqual(position.avg_price_per_unit(), 0.0)
        self.assertEqual(position.total_commission_to_build_position(), 0.0)

    def test_transact_transaction_1(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        quantity = 50
        price = 100
        commission = 5

        position.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.is_closed, False)
        self.assertEqual(position.quantity(), quantity)
        self.assertEqual(position.current_price, 0)  # set by update_price
        self.assertEqual(position.direction, 1)
        self.assertEqual(position.start_time, self.start_time)
        self.assertEqual(position.avg_price_per_unit(), price)  # taken from the list of transactions
        self.assertEqual(position.total_commission_to_build_position(), commission)

    def test_transact_transaction_2(self):
        position = DummyPosition(self.contract, start_time=self.start_time)

        quantity1 = 50
        price1 = 100
        commission1 = 5
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity1, price1, commission1))

        quantity2 = 30
        price2 = 120
        commission2 = 7
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity2, price2, commission2))

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.is_closed, False)
        self.assertEqual(position.quantity(), quantity1 + quantity2)
        self.assertEqual(position.direction, 1)
        self.assertEqual(position.start_time, self.start_time)
        self.assertEqual(position.total_commission_to_build_position(), commission1 + commission2)
        avg_price = (quantity1 * price1 + quantity2 * price2) / (quantity1 + quantity2)
        self.assertEqual(position.avg_price_per_unit(), avg_price)  # taken from the list of transactions

        self.assertEqual(position.current_price, 0)  # set by update_price

    def test_transact_transaction_3(self):
        position = DummyPosition(self.contract, start_time=self.start_time)

        quantity1 = 50
        price1 = 100
        commission1 = 5
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity1, price1, commission1))

        quantity2 = 30
        price2 = 120
        commission2 = 7
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity2, price2, commission2))

        quantity3 = -40
        price3 = 150
        commission3 = 11
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity3, price3, commission3))

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.is_closed, False)
        self.assertEqual(position.quantity(), quantity1 + quantity2 + quantity3)
        self.assertEqual(position.direction, 1)
        self.assertEqual(position.start_time, self.start_time)
        self.assertEqual(position.total_commission_to_build_position(), commission1 + commission2)
        avg_price = (quantity1 * price1 + quantity2 * price2) / (quantity1 + quantity2)
        self.assertEqual(position.avg_price_per_unit(), avg_price)  # taken from the list of transactions

        self.assertEqual(position.current_price, 0)  # set by update_price

    def test_update_price(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        quantity = 50
        price = 100
        commission = 5
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))

        self.assertEqual(position.current_price, 0)  # set by update_price

        bid_price = 110
        position.update_price(bid_price=bid_price, ask_price=bid_price+1)

        self.assertEqual(position.current_price, bid_price)

        bid_price = 120
        position.update_price(bid_price=bid_price, ask_price=bid_price+1)
        self.assertEqual(position.current_price, bid_price)

    def test_without_commission_position(self):
        position = DummyPosition(self.contract, start_time=self.start_time)

        position.transact_transaction(Transaction(self.start_time, self.contract, 50, 100, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, 30, 120, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 175, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, -30, 160, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, 10, 150, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, 10, 170, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 150, 0))
        position.update_price(110, 120)

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position._quantity, 30)
        self.assertEqual(position.current_price, 110)
        self.assertEqual(position.avg_price_per_unit(), 118.0)

    def test_position(self):
        position = DummyPosition(self.contract, start_time=self.start_time)

        position.transact_transaction(Transaction(self.start_time, self.contract, 50, 100, 5))
        position.transact_transaction(Transaction(self.start_time, self.contract, 30, 120, 3))
        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 175, 2))
        position.transact_transaction(Transaction(self.start_time, self.contract, -30, 160, 1))
        position.transact_transaction(Transaction(self.start_time, self.contract, 10, 150, 7))
        position.transact_transaction(Transaction(self.start_time, self.contract, 10, 170, 4))
        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 150, 5))
        position.update_price(110, 120)

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position._quantity, 30)
        self.assertEqual(position.current_price, 110)
        avg_price = (50*100+30*120+10*150+10*170)/100
        self.assertEqual(position.avg_price_per_unit(), avg_price)

    def test_position_close(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        self.assertEqual(position.is_closed, False)
        position.transact_transaction(Transaction(self.start_time, self.contract, 20, 100, 0))
        self.assertEqual(position.is_closed, False)
        position.transact_transaction(Transaction(self.start_time, self.contract, -10, 120, 20))
        self.assertEqual(position.is_closed, False)
        position.transact_transaction(Transaction(self.start_time, self.contract, -10, 110, 20))
        self.assertEqual(position.is_closed, True)

    def test_position_stats_on_close(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        position.transact_transaction(Transaction(self.start_time, self.contract, 20, 100, 0))
        position.update_price(110, 120)
        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 120, 0))

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.is_closed, True)
        self.assertEqual(position.quantity(), 0)
        self.assertEqual(position.current_price, 110)  # set by update_price
        self.assertEqual(position.direction, 0)
        self.assertEqual(position.start_time, self.start_time)
        self.assertEqual(position.avg_price_per_unit(), 0)
        self.assertEqual(position.total_commission_to_build_position(), 0)

    def test_position_direction1(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        self.assertEqual(position.direction, 0)
        position.transact_transaction(Transaction(self.start_time, self.contract, 20, 100, 0))
        self.assertEqual(position.direction, 1)
        position.transact_transaction(Transaction(self.start_time, self.contract, -10, 100, 0))
        self.assertEqual(position.direction, 1)
        position.transact_transaction(Transaction(self.start_time, self.contract, -10, 100, 0))
        self.assertEqual(position.direction, 0)

    def test_position_direction2(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        self.assertEqual(position.direction, 0)

        position.transact_transaction(Transaction(self.start_time, self.contract, 20, 100, 0))
        self.assertEqual(position.direction, 1)

        with self.assertRaises(AssertionError):
            # position does not allow going directly short from long
            position.transact_transaction(Transaction(self.start_time, self.contract, -30, 100, 0))

        position = DummyPosition(self.contract, start_time=self.start_time)
        self.assertEqual(position.direction, 0)

        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 100, 0))
        self.assertEqual(position.direction, -1)

        with self.assertRaises(AssertionError):
            # position does not allow going directly short from long
            position.transact_transaction(Transaction(self.start_time, self.contract, 30, 100, 0))

    def test_closed_position(self):
        position = DummyPosition(self.contract, start_time=self.start_time)
        position.transact_transaction(Transaction(self.start_time, self.contract, 20, 100, 0))
        position.transact_transaction(Transaction(self.start_time, self.contract, -20, 100, 0))

        with self.assertRaises(AssertionError):
            # position is now closed and should not accept new transactions
            position.transact_transaction(Transaction(self.start_time, self.contract, 1, 100, 0))

        with self.assertRaises(AssertionError):
            # position is now closed and should not accept new transactions
            position.transact_transaction(Transaction(self.start_time, self.contract, -1, 100, 0))

        with self.assertRaises(AssertionError):
            # position is now closed
            position.update_price(110, 120)


if __name__ == "__main__":
    unittest.main()
