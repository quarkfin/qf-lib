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

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_series_equal


class DataHandlerMock(object):
    prices = None

    def set_prices(self, prices):
        self.prices = prices

    def get_last_available_price(self, tickers):
        return self.prices


class ContractTickerMapperMock(object):
    def contract_to_ticker(self, contract: Contract):
        return DummyTicker(contract.symbol)


class TestPortfolio(unittest.TestCase):

    def setUp(self):
        self.initial_cash = 1000000  # 1M
        self.contract = Contract('AAPL US Equity', security_type='STK', exchange='NYSE')
        self.contract_size = 75
        self.contract2 = Contract('CTZ9 Comdty', security_type='FUT', exchange='CME', contract_size=self.contract_size)

        self.prices1 = QFSeries(data=[120, 250], index=[DummyTicker("AAPL US Equity"), DummyTicker("CTZ9 Comdty")])
        self.prices_up = QFSeries(data=[130, 270], index=[DummyTicker("AAPL US Equity"), DummyTicker("CTZ9 Comdty")])
        self.prices_down = QFSeries(data=[100, 210], index=[DummyTicker("AAPL US Equity"), DummyTicker("CTZ9 Comdty")])

        self.start_time = str_to_date('2017-01-01')  # dummy time
        self.random_time = str_to_date('2017-02-02')  # dummy time
        self.end_time = str_to_date('2018-02-03')  # dummy time

    def test_initial_cash(self):
        portfolio, _, _ = self.get_portfolio_and_data_handler()
        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.current_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0.0)

    def test_transact_transaction_1(self):
        portfolio, _, _ = self.get_portfolio_and_data_handler()

        quantity = 50
        price = 100
        commission = 5
        portfolio.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        cash_move1 = -price*quantity - commission
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        quantity = -20
        price = 110
        commission = 5
        portfolio.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        cash_move2 = -price*quantity - commission
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1 + cash_move2)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_2(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        quantity = 50
        price = 100
        commission = 5
        portfolio.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))
        dh.set_prices(self.prices1)
        portfolio.update()

        new_price = 120

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        pnl1 = (new_price-price) * quantity - commission
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl1)
        self.assertEqual(portfolio.gross_exposure_of_positions, new_price * quantity)
        cash_move1 = -price * quantity - commission
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        quantity = -20
        price = 110
        commission = 5
        portfolio.transact_transaction(Transaction(self.random_time, self.contract, quantity, price, commission))
        portfolio.update()

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        pnl2 = (new_price-price) * quantity - commission
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl1 + pnl2)

        self.assertEqual(portfolio.gross_exposure_of_positions, new_price * 30)
        cash_move2 = -price * quantity - commission
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1 + cash_move2)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_3(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        quantity = 50
        price = 200
        commission = 7
        portfolio.transact_transaction(Transaction(self.random_time, self.contract2, quantity, price, commission))
        dh.set_prices(self.prices1)
        portfolio.update()

        new_price = 250

        pnl1 = (new_price-price) * quantity * self.contract_size - commission

        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl1)
        self.assertEqual(portfolio.gross_exposure_of_positions, quantity * self.contract_size * new_price)

        cash_move1 = -commission
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        quantity = -20
        commission = 15
        portfolio.transact_transaction(Transaction(self.random_time, self.contract2, quantity, new_price, commission))
        portfolio.update()

        realised_pnl = (new_price-price) * (-quantity) * self.contract_size - commission
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1 + realised_pnl)

        pnl_of_position = (new_price-price) * (50-20) * self.contract_size
        self.assertEqual(portfolio.net_liquidation, portfolio.current_cash + pnl_of_position)

        self.assertEqual(portfolio.gross_exposure_of_positions, (50 - 20) * self.contract_size * new_price)

    def test_transact_transaction_close_position(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        quantity = 50
        price = 200
        commission = 7
        portfolio.transact_transaction(Transaction(self.random_time, self.contract2, quantity, price, commission))
        dh.set_prices(self.prices1)
        portfolio.update()

        quantity = -quantity
        new_price = 250
        portfolio.transact_transaction(Transaction(self.end_time, self.contract2, quantity, new_price, commission))
        portfolio.update()

        pnl = (new_price-price)*(-quantity) * self.contract_size-2*commission

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)
        self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
        self.assertEqual(len(portfolio.open_positions_dict), 0)

    def test_transact_transaction_close_position2(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        quantity = -50
        price = 200
        commission = 7
        portfolio.transact_transaction(Transaction(self.random_time, self.contract2, quantity, price, commission))
        dh.set_prices(self.prices1)
        portfolio.update()

        quantity = -quantity
        new_price = 250
        portfolio.transact_transaction(Transaction(self.end_time, self.contract2, quantity, new_price, commission))
        portfolio.update()

        pnl = (new_price-price)*(-quantity) * self.contract_size-2*commission

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)
        self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
        self.assertEqual(len(portfolio.open_positions_dict), 0)

    def test_transact_transaction_split_position(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        quantity = 50
        price = 200
        commission = 7
        portfolio.transact_transaction(Transaction(self.random_time, self.contract2, quantity, price, commission))
        dh.set_prices(self.prices1)
        portfolio.update()

        remaining_quantity = -10
        new_quantity = -quantity + remaining_quantity
        new_price = 250
        portfolio.transact_transaction(Transaction(self.end_time, self.contract2, new_quantity, new_price, commission))
        portfolio.update()

        pnl = (new_price-price) * quantity * self.contract_size - 2*commission

        self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)

        self.assertEqual(portfolio.gross_exposure_of_positions, abs(remaining_quantity * self.contract_size * new_price))
        self.assertEqual(len(portfolio.open_positions_dict), 1)
        self.assertEqual(len(portfolio.trade_list()), 1)
        self.assertEqual(len(portfolio.transactions_series()), 2)
        positon = list(portfolio.open_positions_dict.values())[0]
        self.assertEqual(positon.quantity(), -10)

    def test_portfolio_eod_series(self):
        expected_values = []
        expected_dates = []

        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)
        expected_values.append(self.initial_cash)
        expected_dates.append(self.start_time)

        # buy contract
        quantity = 50
        price = 250
        commission1 = 7
        new_time = timer.time + RelativeDelta(days=1)

        portfolio.transact_transaction(Transaction(new_time, self.contract2, quantity, price, commission1))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices1)
        portfolio.update(record=True)

        pnl = self.contract_size * quantity * (250-250)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(nav)
        expected_dates.append(new_time)

        # contract goes up in value
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        pnl = self.contract_size * quantity * (270-250)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(nav)
        expected_dates.append(new_time)

        # sell part of the contract
        quantity = -25
        price = 270
        commission2 = 9
        new_time = timer.time + RelativeDelta(days=1)
        portfolio.transact_transaction(Transaction(new_time, self.contract2, quantity, price, commission2))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        nav = nav - commission2
        expected_values.append(nav)
        expected_dates.append(new_time)

        # price goes down
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        pnl1 = self.contract_size * 25 * (270-250)
        pnl2 = self.contract_size * 25 * (210-250)
        nav = self.initial_cash + pnl1 + pnl2 - commission1 - commission2
        expected_values.append(nav)
        expected_dates.append(new_time)

        tms = portfolio.portfolio_eod_series()
        expected_tms = PricesSeries(data=expected_values, index=expected_dates)
        assert_series_equal(expected_tms, tms)

    def test_portfolio_leverage1(self):
        expected_values = []
        expected_dates = []

        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)
        expected_values.append(0)
        expected_dates.append(self.start_time)

        # buy contract
        quantity = 50
        price = 250
        commission1 = 7
        new_time = timer.time + RelativeDelta(days=1)

        portfolio.transact_transaction(Transaction(new_time, self.contract2, quantity, price, commission1))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices1)
        portfolio.update(record=True)

        gross_value = self.contract_size * quantity * price
        pnl = self.contract_size * quantity * (250 - 250)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # contract goes up in value
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        gross_value = self.contract_size * quantity * 270
        pnl = self.contract_size * quantity * (270 - 250)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # sell part of the contract
        quantity = -30
        price = 270
        commission2 = 9
        new_time = timer.time + RelativeDelta(days=1)
        portfolio.transact_transaction(Transaction(new_time, self.contract2, quantity, price, commission2))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        gross_value = self.contract_size * 20 * 270
        nav = nav - commission2
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # price goes down
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        gross_value = self.contract_size * 20 * 210
        pnl1 = self.contract_size * 30 * (270 - 250)
        pnl2 = self.contract_size * 20 * (210 - 250)
        nav = self.initial_cash + pnl1 + pnl2 - commission1 - commission2
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        leverage_tms = portfolio.leverage_series()
        expected_tms = QFSeries(data=expected_values, index=expected_dates)

        print(leverage_tms)
        print(expected_tms)
        assert_series_equal(expected_tms, leverage_tms)

    def test_portfolio_leverage2(self):
        expected_values = []
        expected_dates = []

        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)
        expected_values.append(0)
        expected_dates.append(self.start_time)

        # buy contract
        quantity = 500
        price = 120
        commission1 = 7
        new_time = timer.time + RelativeDelta(days=1)

        portfolio.transact_transaction(Transaction(new_time, self.contract, quantity, price, commission1))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices1)
        portfolio.update(record=True)

        gross_value = quantity * price
        pnl = quantity * (120 - 120)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # contract goes up in value
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        gross_value = quantity * 130
        pnl = quantity * (130 - 120)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # sell part of the contract
        quantity = -300
        price = 130
        commission2 = 9
        new_time = timer.time + RelativeDelta(days=1)
        portfolio.transact_transaction(Transaction(new_time, self.contract, quantity, price, commission2))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        gross_value = 200 * 130
        nav = nav - commission2
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # price goes down
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        gross_value = 200 * 100
        pnl1 = 300 * (130 - 120)
        pnl2 = 200 * (100 - 120)
        nav = self.initial_cash + pnl1 + pnl2 - commission1 - commission2
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        leverage_tms = portfolio.leverage_series()
        expected_tms = QFSeries(data=expected_values, index=expected_dates)

        print(leverage_tms)
        print(expected_tms)
        assert_series_equal(expected_tms, leverage_tms)

    def test_portfolio_history(self):
        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)

        # buy contract
        quantity = 50
        price = 250
        commission1 = 7
        new_time = timer.time + RelativeDelta(days=1)

        portfolio.transact_transaction(Transaction(new_time, self.contract2, quantity, price, commission1))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices1)
        portfolio.update(record=True)

        # buy another instrument - price goes up
        portfolio.transact_transaction(Transaction(new_time, self.contract, 20, 120, commission1))
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        # sell part of the contract
        quantity = -30
        price = 270
        commission2 = 9
        new_time = timer.time + RelativeDelta(days=1)
        portfolio.transact_transaction(Transaction(new_time, self.contract2, quantity, price, commission2))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        # price goes down
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        asset_history = portfolio.positions_eod_history()
        self.assertEqual(asset_history.shape, (5, 2))
        self.assertEqual(asset_history.iloc[4, 0], 315000)
        self.assertEqual(asset_history.iloc[4, 1], 2000)

    def test_portfolio_transactions_series(self):
        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)

        commission = 7

        # buy contracts
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract2, 50, 250, commission))
        dh.set_prices(self.prices1)
        portfolio.update(record=True)

        # buy another instrument - price goes up
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 20, 120, commission))
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        # sell part of the contract
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -5, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -2, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -3, 270, commission))
        portfolio.update(record=True)

        # sell part of the contract - with going into opposite direction
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -20, 271, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract2, -10, 130, commission))
        portfolio.update(record=True)

        # buy back part of the contract
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 5, 210, commission))
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        transactions = portfolio.transactions_series()

        self.assertEqual(transactions.shape[0], 8)
        t = transactions.iloc[5]
        self.assertEqual(t.price, 271)
        self.assertEqual(t.quantity, -20)

    def test_portfolio_trade_list(self):
        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)

        commission = 7

        # buy contracts
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract2, 50, 120, commission))
        dh.set_prices(self.prices1)
        portfolio.update(record=True)

        # buy another instrument - price goes up
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 20, 120, commission))
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        # sell part of the contract
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -5, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -2, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -3, 270, commission))
        portfolio.update(record=True)

        # sell part of the contract - with going into opposite direction
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, -200, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract2, -10, 130, commission))
        portfolio.update(record=True)

        # buy again part of the contract
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 5, 210, commission))
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        #
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 1, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 2, 270, commission))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 3, 270, commission))
        portfolio.update(record=True)

        #
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.contract, 200, 270, commission))
        portfolio.update(record=True)

        trades = portfolio.trade_list()
        for t in trades:
            print(t)

        self.assertEqual(len(trades), 10)
        t = trades[4]
        self.assertEqual(t.pnl, 7491.6)

    # noinspection PyTypeChecker
    def get_portfolio_and_data_handler(self):
        data_handler = DataHandlerMock()
        contract_mapper = ContractTickerMapperMock()
        timer = SettableTimer()
        timer.set_current_time(self.start_time)

        portfolio = Portfolio(data_handler, self.initial_cash, timer, contract_mapper)
        return portfolio, data_handler, timer

if __name__ == "__main__":
    unittest.main()
