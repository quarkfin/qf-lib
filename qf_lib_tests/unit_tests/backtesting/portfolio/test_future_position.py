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
from qf_lib.backtesting.portfolio.backtest_future_position import BacktestFuturePosition
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class TestEquityPosition(unittest.TestCase):

    def setUp(self):
        self.contract_size = 75
        self.contract = Contract('CTZ9 Comdty', security_type='FUT', exchange='CME', contract_size=self.contract_size)
        self.start_time = str_to_date('2017-01-01')  # dummy time
        self.random_time = str_to_date('2017-02-02')  # dummy time
        self.end_time = str_to_date('2018-02-03')  # dummy time

    def test_creating_empty_position(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)
        self.assertEqual(position.market_value(), 0)

    def test_transact_transaction_1(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)
        quantity = 50
        price = 100
        commission = 5

        cash_move = position.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))
        self.assertEqual(cash_move, -commission)

    def test_transact_transaction_2(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)
        quantity = -50
        price = 100
        commission = 5

        cash_move = position.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))
        self.assertEqual(cash_move, -commission)

    def test_transact_transaction_3(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)

        quantity1 = 50
        price1 = 100
        commission1 = 5
        cash_move1 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity1, price1,
                                                               commission1))
        self.assertEqual(cash_move1, -commission1)

        quantity2 = -30
        price2 = 120
        commission2 = 7
        cash_move2 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity2, price2,
                                                               commission2))
        expected_move = (price2 - price1) * (-quantity2) * self.contract_size - commission2
        self.assertEqual(cash_move2, expected_move)

    def test_transact_transaction_4(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)

        quantity1 = -50
        price1 = 100
        commission1 = 5
        cash_move1 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity1, price1,
                                                               commission1))
        self.assertEqual(cash_move1, -commission1)

        quantity2 = 30
        price2 = 120
        commission2 = 7
        cash_move2 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity2, price2,
                                                               commission2))
        expected_move = (price2 - price1) * (-quantity2) * self.contract_size - commission2
        self.assertEqual(cash_move2, expected_move)

    def test_transact_transaction_5(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)

        quantity1 = 50
        price1 = 100
        commission1 = 5
        cash_move1 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity1, price1,
                                                               commission1))
        self.assertEqual(cash_move1, -commission1)

        quantity1 = 50
        price1 = 110
        commission1 = 5
        cash_move1 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity1, price1,
                                                               commission1))
        self.assertEqual(cash_move1, -commission1)

        quantity2 = -30
        price2 = 120
        commission2 = 7
        cash_move2 = position.transact_transaction(Transaction(self.random_time, self.contract, quantity2, price2,
                                                               commission2))
        expected_move = (price2 - 105) * (-quantity2) * self.contract_size - commission2
        self.assertEqual(cash_move2, expected_move)

    def test_market_value(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)
        quantity = 50
        price = 100
        commission = 5
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))

        self.assertEqual(position.market_value(), 0)  # before update_price

        bid_price = 110
        position.update_price(bid_price=bid_price, ask_price=bid_price + 1)

        market_value = (bid_price - price) * quantity * self.contract_size
        self.assertEqual(position.market_value(), market_value)

        bid_price = 120
        position.update_price(bid_price=bid_price, ask_price=bid_price + 1)
        market_value = (bid_price - price) * quantity * self.contract_size
        self.assertEqual(position.market_value(), market_value)

    def test_market_value2(self):
        position = BacktestFuturePosition(self.contract, start_time=self.start_time)
        quantity = -50
        price = 100
        commission = 5
        position.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))

        self.assertEqual(position.market_value(), 0)  # before update_price

        bid_price = 110
        ask_price = 120
        position.update_price(bid_price=bid_price, ask_price=ask_price)

        market_value = (ask_price - price) * quantity * self.contract_size
        self.assertEqual(position.market_value(), market_value)

        bid_price = 120
        ask_price = 130
        position.update_price(bid_price=bid_price, ask_price=ask_price)

        market_value = (ask_price - price) * quantity * self.contract_size
        self.assertEqual(position.market_value(), market_value)


if __name__ == "__main__":
    unittest.main()
