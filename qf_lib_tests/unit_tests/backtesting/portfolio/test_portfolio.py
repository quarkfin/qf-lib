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

from numpy.core.umath import sign

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
        if tickers:
            return self.prices[tickers]
        else:
            return None


class ContractTickerMapperMock(object):
    def contract_to_ticker(self, contract: Contract):
        return DummyTicker(contract.symbol)


class TestPortfolio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.initial_cash = 1000000  # 1M
        cls.contract = Contract('AAPL US Equity', security_type='STK', exchange='NYSE')
        cls.contract_size = 75
        cls.fut_contract = Contract('CTZ9 Comdty', security_type='FUT', exchange='CME', contract_size=cls.contract_size)

        tickers = [DummyTicker(cls.contract.symbol), DummyTicker(cls.fut_contract.symbol)]
        cls.prices_series = QFSeries(data=[120, 250], index=tickers)
        cls.prices_up = QFSeries(data=[130, 270], index=tickers)
        cls.prices_down = QFSeries(data=[100, 210], index=tickers)

        cls.start_time = str_to_date('2017-01-01')
        cls.random_time = str_to_date('2017-02-02')
        cls.end_time = str_to_date('2018-02-03')

    def test_initial_cash(self):
        portfolio, _, _ = self.get_portfolio_and_data_handler()
        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.current_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0.0)

    @staticmethod
    def _cash_move(transaction: Transaction):
        return -1 * transaction.price * transaction.quantity * transaction.contract.contract_size - transaction.commission

    def test_transact_transaction_1(self):
        portfolio, _, _ = self.get_portfolio_and_data_handler()

        transaction = Transaction(self.random_time, self.contract, quantity=50, price=100, commission=5)
        portfolio.transact_transaction(transaction)

        cash_move_1 = self._cash_move(transaction)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        transaction = Transaction(self.random_time, self.contract, quantity=-20, price=110, commission=5)
        portfolio.transact_transaction(transaction)

        cash_move_2 = self._cash_move(transaction)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1 + cash_move_2)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_2(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()
        contract = self.contract
        ticker = portfolio.contract_ticker_mapper.contract_to_ticker(contract)

        # First transaction
        transaction_1 = Transaction(self.random_time, contract, quantity=50, price=100, commission=5)
        portfolio.transact_transaction(transaction_1)

        # Set new prices
        dh.set_prices(self.prices_series)
        portfolio.update()

        # Get the new price of the contract
        new_price = dh.get_last_available_price(ticker)

        pnl_1 = (new_price - transaction_1.price) * transaction_1.quantity * transaction_1.contract.contract_size \
            - transaction_1.commission
        cash_move1 = self._cash_move(transaction_1)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl_1)
        self.assertEqual(portfolio.gross_exposure_of_positions, new_price * transaction_1.quantity)
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        # Second transaction
        transaction_2 = Transaction(self.random_time, contract, quantity=-20, price=110, commission=5)
        portfolio.transact_transaction(transaction_2)
        portfolio.update()

        pnl_2 = (new_price - transaction_2.price) * transaction_2.quantity * transaction_2.contract.contract_size \
            - transaction_2.commission
        cash_move_2 = self._cash_move(transaction_2)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl_1 + pnl_2)

        position = portfolio.open_positions_dict[contract]
        self.assertEqual(portfolio.gross_exposure_of_positions,
                         new_price * position.quantity() * contract.contract_size)
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1 + cash_move_2)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_3(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()
        contract = self.fut_contract
        ticker = portfolio.contract_ticker_mapper.contract_to_ticker(contract)

        # First transaction
        transaction_1 = Transaction(self.random_time, contract, quantity=50, price=200, commission=7)
        portfolio.transact_transaction(transaction_1)

        # Set new prices
        dh.set_prices(self.prices_series)
        portfolio.update()

        # Get the new price of the contract
        new_price = dh.get_last_available_price(ticker)

        pnl_1 = (new_price - transaction_1.price) * transaction_1.quantity * transaction_1.contract.contract_size \
            - transaction_1.commission
        cash_move_1 = -transaction_1.commission

        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl_1)
        self.assertEqual(portfolio.gross_exposure_of_positions,
                         transaction_1.quantity * contract.contract_size * new_price)
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        # Second transaction
        transaction_2 = Transaction(self.random_time, contract, quantity=-20, price=new_price, commission=15)
        portfolio.transact_transaction(transaction_2)
        portfolio.update()

        # Computed the realized pnl, which is already included in the portfolio current cash - it may not be the same as
        # the pnl of the trade, as the commission trades
        trade_size = min(abs(transaction_1.quantity), abs(transaction_2.quantity))

        realised_pnl = (-1) * transaction_1.price * trade_size * sign(transaction_1.quantity) * contract.contract_size
        realised_pnl += (-1) * transaction_2.price * trade_size * sign(transaction_2.quantity) * contract.contract_size
        realised_pnl -= transaction_2.commission  # Only transaction2 commission is yet realised

        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1 + realised_pnl)

        position = portfolio.open_positions_dict[contract]
        position_unrealised_pnl = position.unrealised_pnl
        self.assertEqual(portfolio.net_liquidation, portfolio.current_cash + position_unrealised_pnl)

        exposure = position.quantity() * contract.contract_size * new_price
        self.assertEqual(portfolio.gross_exposure_of_positions, position.total_exposure())
        self.assertEqual(exposure, position.total_exposure())

    def test_transact_transaction_close_position_2_transactions(self):

        for quantity in (-50, 50):
            portfolio, dh, _ = self.get_portfolio_and_data_handler()
            contract = self.fut_contract
            ticker = portfolio.contract_ticker_mapper.contract_to_ticker(contract)

            all_commissions = 0.0

            transaction_1 = Transaction(self.random_time, contract, quantity=quantity, price=200, commission=7)
            portfolio.transact_transaction(transaction_1)
            all_commissions += transaction_1.commission
            dh.set_prices(self.prices_series)
            portfolio.update()

            new_price = dh.get_last_available_price(ticker)
            transaction_2 = Transaction(self.end_time, contract, quantity=-transaction_1.quantity,
                                        price=new_price,
                                        commission=transaction_1.commission)
            portfolio.transact_transaction(transaction_2)
            all_commissions += transaction_2.commission
            portfolio.update()

            pnl = (new_price - transaction_1.price) * transaction_1.quantity * contract.contract_size \
                - all_commissions

            self.assertEqual(portfolio.initial_cash, self.initial_cash)
            self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)
            self.assertEqual(portfolio.gross_exposure_of_positions, 0)
            self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
            self.assertEqual(len(portfolio.open_positions_dict), 0)

            # Test generated trades - exactly one trade should be generated
            trades_list = portfolio.trade_list()
            self.assertEqual(len(trades_list), 1)

            trade = trades_list[0]
            self.assertEqual(trade.pnl, pnl)
            self.assertEqual(trade.commission, all_commissions)

    def test_transact_transaction_split_position(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()
        contract = self.fut_contract
        ticker = portfolio.contract_ticker_mapper.contract_to_ticker(contract)

        # Transact two transaction, which will result in transactions splitting
        quantity_after_first_transaction = 50
        quantity_after_second_transaction = -10
        initial_price = 200
        commission = 7

        # Transact the initial transaction
        transaction_1 = Transaction(self.random_time, contract, quantity_after_first_transaction,
                                    initial_price, commission)
        portfolio.transact_transaction(transaction_1)

        # Set new prices
        dh.set_prices(self.prices_series)
        new_price = dh.get_last_available_price(ticker)  # == 250
        portfolio.update()

        # Transact the second transaction
        transaction_quantity = -quantity_after_first_transaction + quantity_after_second_transaction
        transaction_2 = Transaction(self.end_time, contract, transaction_quantity, new_price, commission)
        portfolio.transact_transaction(transaction_2)
        portfolio.update()

        # Compute the pnl of the position, which was closed
        quantity = max(abs(quantity_after_first_transaction), abs(quantity_after_second_transaction))
        quantity *= sign(quantity_after_first_transaction)
        all_commissions = transaction_1.commission + transaction_2.commission
        pnl = (new_price - initial_price) * quantity * contract.contract_size - all_commissions

        position = list(portfolio.open_positions_dict.values())[0]
        self.assertEqual(position.quantity(), -10)

        trade = portfolio.trade_list()[0]
        self.assertEqual(trade.pnl - position.remaining_total_commission(), pnl)

        self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)

        self.assertEqual(portfolio.gross_exposure_of_positions,
                         abs(quantity_after_second_transaction * self.contract_size * new_price))
        self.assertEqual(len(portfolio.open_positions_dict), 1)
        self.assertEqual(len(portfolio.trade_list()), 1)
        self.assertEqual(len(portfolio.transactions_series()), 2)

    def test_transact_transaction_split_and_close(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()
        contract = self.fut_contract
        ticker = portfolio.contract_ticker_mapper.contract_to_ticker(contract)

        # Transact the initial transaction
        transactions = []
        quantity = 50

        # Set initial price for the given ticker
        dh.set_prices(self.prices_down)
        price_1 = dh.get_last_available_price(ticker)  # == 210

        initial_transaction = Transaction(self.random_time, contract, quantity=quantity, price=price_1,
                                          commission=10)
        portfolio.transact_transaction(initial_transaction)
        transactions.append(initial_transaction)
        portfolio.update()

        # Change of price for the given ticker
        dh.set_prices(self.prices_series)
        price_2 = dh.get_last_available_price(ticker)  # == 250

        transaction_to_split = Transaction(self.random_time, contract, quantity=(-2) * quantity,
                                           price=price_2, commission=18)
        portfolio.transact_transaction(transaction_to_split)
        transactions.append(transaction_to_split)
        portfolio.update()

        trade_pnl = (price_2 - price_1) * contract.contract_size * quantity
        trade_pnl -= initial_transaction.commission
        trade_pnl -= transaction_to_split.commission * abs(initial_transaction.quantity / transaction_to_split.quantity)
        trade = portfolio.trade_list()[0]
        self.assertEqual(trade_pnl, trade.pnl)

        # The sum of cash moves for both transactions should be equal to pnl of the trade - remaining_total_commission
        # (because the sum of cash_move already considers both commissions, where the trade.pnl, as the position is not
        # closed, does not consider all of the commissions yet) - total_exposure of the remaining position
        position = portfolio.open_positions_dict[contract]
        cash_move = sum(self._cash_move(t) for t in transactions)
        self.assertEqual(trade.pnl - position.total_exposure() - position.remaining_total_commission(), cash_move)

        # Change of price for the given ticker
        dh.set_prices(self.prices_series)
        price_3 = dh.get_last_available_price(ticker)  # == 270
        closing_transaction = Transaction(self.random_time, contract, quantity=quantity,
                                          price=price_3, commission=5)
        portfolio.transact_transaction(closing_transaction)
        transactions.append(closing_transaction)
        portfolio.update()

        # All positions should be closed at this moment
        self.assertEqual(len(portfolio.open_positions_dict), 0)
        # Two trades should have been created
        self.assertEqual(len(portfolio.trade_list()), 2)

        # As the positions are closed, the sum of commissions for transactions should be equal to the sum of commissions
        # of trades
        all_transactions_commissions = sum(t.commission for t in transactions)
        all_trades_commissions = sum(trade.commission for trade in portfolio.trade_list())
        self.assertEqual(all_transactions_commissions, all_trades_commissions)

        # As positions are closed, the sum of all cash movements should be equal to
        cash_move = sum(self._cash_move(t) for t in transactions)
        trades_pnl = sum(trade.pnl for trade in portfolio.trade_list())
        self.assertEqual(cash_move, trades_pnl)

    def test_portfolio_eod_series(self):
        expected_portfolio_eod_series = PricesSeries()

        # Empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)
        expected_portfolio_eod_series[timer.time] = self.initial_cash

        contract = self.fut_contract
        ticker = portfolio.contract_ticker_mapper.contract_to_ticker(contract)

        # Buy contract
        self._shift_timer_to_next_day(timer)
        transaction_1 = Transaction(timer.time, contract, quantity=50, price=250, commission=7)
        portfolio.transact_transaction(transaction_1)
        dh.set_prices(self.prices_series)
        portfolio.update(record=True)

        position = portfolio.open_positions_dict[contract]

        price_1 = dh.get_last_available_price(ticker)
        pnl = contract.contract_size * transaction_1.quantity * (price_1 - transaction_1.price)
        nav = self.initial_cash + pnl - transaction_1.commission
        expected_portfolio_eod_series[timer.time] = nav

        # Contract goes up in value
        self._shift_timer_to_next_day(timer)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        price_2 = dh.get_last_available_price(ticker)  # == 270
        pnl = contract.contract_size * transaction_1.quantity * (price_2 - price_1)
        nav += pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Sell part of the contract
        self._shift_timer_to_next_day(timer)
        transaction_2 = Transaction(timer.time, contract, quantity=-25, price=price_2, commission=19)
        portfolio.transact_transaction(transaction_2)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        pnl = (transaction_2.price - price_2) * transaction_2.quantity * contract.contract_size - transaction_2.commission
        nav += pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Price goes down
        self._shift_timer_to_next_day(timer)
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        price_3 = dh.get_last_available_price(ticker)  # == 210
        pnl2 = contract.contract_size * position.quantity() * (price_3 - price_2)
        nav += pnl2
        expected_portfolio_eod_series[timer.time] = nav

        tms = portfolio.portfolio_eod_series()
        assert_series_equal(expected_portfolio_eod_series, tms)

    @staticmethod
    def _shift_timer_to_next_day(timer: SettableTimer):
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)

    def test_portfolio_leverage1(self):
        portfolio, dh, timer = self.get_portfolio_and_data_handler()

        expected_leverage_series = QFSeries()
        nav = self.initial_cash
        contract = self.fut_contract
        position = None

        def record_leverage():
            expected_leverage_series[timer.now()] = position.total_exposure() / nav

        # Empty portfolio
        portfolio.update(record=True)
        expected_leverage_series[self.start_time] = 0

        # Buy contract
        self._shift_timer_to_next_day(timer)
        transaction_1 = Transaction(timer.now(), contract, quantity=50, price=250, commission=7)
        portfolio.transact_transaction(transaction_1)
        dh.set_prices(self.prices_series)
        portfolio.update(record=True)

        position = portfolio.open_positions_dict[contract]

        # Compute the leverage
        pnl = contract.contract_size * transaction_1.quantity * (position.current_price - transaction_1.price)
        nav += pnl - transaction_1.commission
        record_leverage()

        # Contract goes up in value
        self._shift_timer_to_next_day(timer)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        # Compute the leverage
        price_after_increase = position.current_price
        pnl = contract.contract_size * transaction_1.quantity * (price_after_increase - transaction_1.price)
        nav = self.initial_cash + pnl - transaction_1.commission
        record_leverage()

        # Sell part of the contract
        self._shift_timer_to_next_day(timer)
        transaction_2 = Transaction(timer.time, contract, quantity=-30, price=position.current_price, commission=9)
        portfolio.transact_transaction(transaction_2)
        dh.set_prices(self.prices_up)
        portfolio.update(record=True)

        # Compute the leverage
        pnl = (transaction_2.price - price_after_increase) * transaction_2.quantity * contract.contract_size
        nav += pnl - transaction_2.commission
        record_leverage()

        # Price goes down
        self._shift_timer_to_next_day(timer)
        dh.set_prices(self.prices_down)
        portfolio.update(record=True)

        pnl = contract.contract_size * position.quantity() * (position.current_price - transaction_2.price)
        nav += pnl
        record_leverage()

        leverage_tms = portfolio.leverage_series()
        assert_series_equal(expected_leverage_series, leverage_tms)

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
        dh.set_prices(self.prices_series)
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

        portfolio.transact_transaction(Transaction(new_time, self.fut_contract, quantity, price, commission1))
        timer.set_current_time(new_time)
        dh.set_prices(self.prices_series)
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
        portfolio.transact_transaction(Transaction(new_time, self.fut_contract, quantity, price, commission2))
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
        self.assertEqual(asset_history.iloc[4, 0].total_exposure, 315000)
        self.assertEqual(asset_history.iloc[4, 1].total_exposure, 2000)

    def test_portfolio_transactions_series(self):
        # empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)

        commission = 7

        # buy contracts
        timer.set_current_time(timer.time + RelativeDelta(days=1))
        portfolio.transact_transaction(Transaction(timer.time, self.fut_contract, 50, 250, commission))
        dh.set_prices(self.prices_series)
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
        portfolio.transact_transaction(Transaction(timer.time, self.fut_contract, -10, 130, commission))
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
        portfolio.transact_transaction(Transaction(timer.time, self.fut_contract, 50, 120, commission))
        dh.set_prices(self.prices_series)
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
        portfolio.transact_transaction(Transaction(timer.time, self.fut_contract, -10, 130, commission))
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

        self.assertEqual(len(trades), 10)
        t = trades[4]
        self.assertEqual(t.pnl, 7491.6)

    def test_trades_commissions(self):
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        dh.set_prices(self.prices_series)
        portfolio.update(record=True)
        trades_commissions = []

        price = 10.0
        commission1 = 16.0
        quantity1 = 8
        transaction1 = Transaction(timer.time, self.contract, quantity1, price, commission1)
        portfolio.transact_transaction(transaction1)
        portfolio.update(record=True)

        commission2 = 10.0
        quantity2 = -2
        transaction2 = Transaction(timer.time, self.contract, quantity2, price, commission2)
        # A Trade should be created with following commission
        trade_commission = commission1 * (abs(quantity2) / abs(quantity1)) + commission2
        trades_commissions.append(trade_commission)
        portfolio.transact_transaction(transaction2)
        portfolio.update(record=True)

        commission3 = 12.0
        quantity3 = 4
        transaction3 = Transaction(timer.time, self.contract, quantity3, price, commission3)
        portfolio.transact_transaction(transaction3)
        portfolio.update(record=True)

        commission4 = 11.0
        quantity4 = -10
        transaction4 = Transaction(timer.time, self.contract, quantity4, price, commission4)
        # A Trade should be created with following commission
        trade_commission = commission1 * (1 - abs(quantity2) / abs(quantity1)) + commission3 + commission4
        trades_commissions.append(trade_commission)
        portfolio.transact_transaction(transaction4)
        portfolio.update(record=True)

        self.assertCountEqual(trades_commissions, [t.commission for t in portfolio.trade_list()])
        self.assertEqual(sum(trades_commissions), commission1 + commission2 + commission3 + commission4)

    def test_trades_commissions_transaction_split(self):
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        dh.set_prices(self.prices_series)
        portfolio.update(record=True)
        trades_commissions = []

        price = 10.0
        commission1 = 16.0
        quantity1 = 8
        transaction1 = Transaction(timer.time, self.contract, quantity1, price, commission1)
        portfolio.transact_transaction(transaction1)
        portfolio.update(record=True)

        commission2 = 10.0
        quantity2 = -2
        transaction2 = Transaction(timer.time, self.contract, quantity2, price, commission2)
        # A Trade should be created with following commission
        trade_commission = commission1 * (abs(quantity2) / abs(quantity1)) + commission2
        trades_commissions.append(trade_commission)
        portfolio.transact_transaction(transaction2)
        portfolio.update(record=True)

        commission3 = 12.0
        quantity3 = -24
        transaction3 = Transaction(timer.time, self.contract, quantity3, price, commission3)
        # A Trade should be created with following commission
        trade_commission = commission1 * (1 - abs(quantity2) / abs(quantity1))
        trade_commission += commission3 * (quantity1 + quantity2) / abs(quantity3)
        trades_commissions.append(trade_commission)
        # This transaction should result in a new position being open
        portfolio.transact_transaction(transaction3)
        portfolio.update(record=True)

        commission4 = 12.0
        quantity4 = 18
        transaction4 = Transaction(timer.time, self.contract, quantity4, price, commission4)
        # A Trade should be created with following commission
        trade_commission = commission3 * quantity4 / abs(quantity3) + commission4
        trades_commissions.append(trade_commission)
        # This transaction should result in a new position being open
        portfolio.transact_transaction(transaction4)
        portfolio.update(record=True)

        self.assertCountEqual(trades_commissions, [t.commission for t in portfolio.trade_list()])
        self.assertEqual(sum(trades_commissions), commission1 + commission2 + commission3 + commission4)

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
