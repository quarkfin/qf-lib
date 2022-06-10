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
from unittest.mock import Mock

from numpy.core.umath import sign

from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestPortfolio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.initial_cash = 1000000  # 1M
        cls.ticker = DummyTicker('AAPL US Equity', SecurityType.STOCK)
        cls.point_value = 75
        cls.fut_ticker = DummyTicker('CTZ9 Comdty', SecurityType.FUTURE, cls.point_value)

        tickers = [cls.ticker, cls.fut_ticker]
        cls.prices_series = QFSeries(data=[120, 250], index=tickers)
        cls.prices_up = QFSeries(data=[130, 270], index=tickers)
        cls.prices_down = QFSeries(data=[100, 210], index=tickers)

        cls.start_time = str_to_date('2017-01-01')
        cls.random_time = str_to_date('2017-02-02')
        cls.end_time = str_to_date('2018-02-03')
        cls.trades_generator = TradesGenerator()

    def setUp(self) -> None:
        self.data_handler_prices = None

    def get_portfolio_and_data_handler(self):
        data_handler = Mock(spec=DataHandler)
        data_handler.get_last_available_price.side_effect = lambda tickers: self.data_handler_prices[tickers] \
            if tickers else None

        timer = SettableTimer()
        timer.set_current_time(self.start_time)

        portfolio = Portfolio(data_handler, self.initial_cash, timer)
        return portfolio, data_handler, timer

    def test_initial_cash(self):
        portfolio, _, _ = self.get_portfolio_and_data_handler()
        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.current_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0.0)

    @staticmethod
    def _cash_move(transaction: Transaction):
        return -1 * transaction.price * transaction.quantity * transaction.ticker.point_value - transaction.commission

    def test_transact_transaction_1(self):
        portfolio, _, _ = self.get_portfolio_and_data_handler()

        transaction = Transaction(self.random_time, self.ticker, quantity=50, price=100, commission=5)
        portfolio.transact_transaction(transaction)

        cash_move_1 = self._cash_move(transaction)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        transaction = Transaction(self.random_time, self.ticker, quantity=-20, price=110, commission=5)
        portfolio.transact_transaction(transaction)

        cash_move_2 = self._cash_move(transaction)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1 + cash_move_2)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_2(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        # First transaction
        transaction_1 = Transaction(self.random_time, self.ticker, quantity=50, price=100, commission=5)
        portfolio.transact_transaction(transaction_1)

        # Set new prices
        self.data_handler_prices = self.prices_series
        portfolio.update()

        # Get the new price of the contract
        new_price = dh.get_last_available_price(self.ticker)

        pnl_1 = (new_price - transaction_1.price) * transaction_1.quantity * transaction_1.ticker.point_value \
            - transaction_1.commission
        cash_move1 = self._cash_move(transaction_1)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl_1)
        self.assertEqual(portfolio.gross_exposure_of_positions, new_price * transaction_1.quantity)
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        # Second transaction
        transaction_2 = Transaction(self.random_time, self.ticker, quantity=-20, price=110, commission=5)
        portfolio.transact_transaction(transaction_2)
        portfolio.update()

        pnl_2 = (new_price - transaction_2.price) * transaction_2.quantity * transaction_2.ticker.point_value \
            - transaction_2.commission
        cash_move_2 = self._cash_move(transaction_2)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl_1 + pnl_2)

        position = portfolio.open_positions_dict[self.ticker]
        self.assertEqual(portfolio.gross_exposure_of_positions,
                         new_price * position.quantity() * self.ticker.point_value)
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move1 + cash_move_2)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_3(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        # First transaction
        transaction_1 = Transaction(self.random_time, self.fut_ticker, quantity=50, price=200, commission=7)
        portfolio.transact_transaction(transaction_1)

        # Set new prices
        self.data_handler_prices = self.prices_series
        portfolio.update()

        # Get the new price of the contract
        new_price = dh.get_last_available_price(self.fut_ticker)

        pnl_1 = (new_price - transaction_1.price) * transaction_1.quantity * transaction_1.ticker.point_value \
            - transaction_1.commission
        cash_move_1 = -transaction_1.commission

        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl_1)
        self.assertEqual(portfolio.gross_exposure_of_positions,
                         transaction_1.quantity * self.fut_ticker.point_value * new_price)
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

        # Second transaction
        transaction_2 = Transaction(self.random_time, self.fut_ticker, quantity=-20, price=new_price, commission=15)
        portfolio.transact_transaction(transaction_2)
        portfolio.update()

        # Computed the realized pnl, which is already included in the portfolio current cash - it may not be the same as
        # the pnl of the trade, as the commission trades
        trade_size = min(abs(transaction_1.quantity), abs(transaction_2.quantity))

        realised_pnl = (-1) * transaction_1.price * trade_size * sign(
            transaction_1.quantity) * self.fut_ticker.point_value
        realised_pnl += (-1) * transaction_2.price * trade_size * sign(
            transaction_2.quantity) * self.fut_ticker.point_value
        realised_pnl -= transaction_2.commission  # Only transaction2 commission is yet realised

        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1 + realised_pnl)

        position = portfolio.open_positions_dict[self.fut_ticker]
        position_unrealised_pnl = position.unrealised_pnl
        self.assertEqual(portfolio.net_liquidation, portfolio.current_cash + position_unrealised_pnl)

        exposure = position.quantity() * self.fut_ticker.point_value * new_price
        self.assertEqual(portfolio.gross_exposure_of_positions, position.total_exposure())
        self.assertEqual(exposure, position.total_exposure())

    def test_transact_transaction_close_position_2_transactions(self):
        for quantity in (-50, 50):
            portfolio, dh, _ = self.get_portfolio_and_data_handler()
            all_commissions = 0.0

            transaction_1 = Transaction(self.random_time, self.fut_ticker, quantity=quantity, price=200, commission=7)
            portfolio.transact_transaction(transaction_1)
            all_commissions += transaction_1.commission
            self.data_handler_prices = self.prices_series
            portfolio.update()

            new_price = dh.get_last_available_price(self.fut_ticker)
            transaction_2 = Transaction(self.end_time, self.fut_ticker, quantity=-transaction_1.quantity,
                                        price=new_price,
                                        commission=transaction_1.commission)
            portfolio.transact_transaction(transaction_2)
            all_commissions += transaction_2.commission
            portfolio.update()

            pnl = (new_price - transaction_1.price) * transaction_1.quantity * self.fut_ticker.point_value \
                - all_commissions

            self.assertEqual(portfolio.initial_cash, self.initial_cash)
            self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)
            self.assertEqual(portfolio.gross_exposure_of_positions, 0)
            self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
            self.assertEqual(len(portfolio.open_positions_dict), 0)

    def test_transact_transaction_split_position(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        # Transact two transaction, which will result in transactions splitting
        quantity_after_first_transaction = 50
        quantity_after_second_transaction = -10
        initial_price = 200
        commission = 7

        # Transact the initial transaction
        transaction_1 = Transaction(self.random_time, self.fut_ticker, quantity_after_first_transaction,
                                    initial_price, commission)
        portfolio.transact_transaction(transaction_1)

        # Set new prices
        self.data_handler_prices = self.prices_series
        new_price = dh.get_last_available_price(self.fut_ticker)  # == 250
        portfolio.update()

        # Transact the second transaction
        transaction_quantity = -quantity_after_first_transaction + quantity_after_second_transaction
        transaction_2 = Transaction(self.end_time, self.fut_ticker, transaction_quantity, new_price, commission)
        portfolio.transact_transaction(transaction_2)
        portfolio.update()

        # Compute the pnl of the position, which was closed
        quantity = max(abs(quantity_after_first_transaction), abs(quantity_after_second_transaction))
        quantity *= sign(quantity_after_first_transaction)
        all_commissions = transaction_1.commission + transaction_2.commission
        pnl = (new_price - initial_price) * quantity * self.fut_ticker.point_value - all_commissions

        position = list(portfolio.open_positions_dict.values())[0]
        self.assertEqual(position.quantity(), -10)

        self.assertEqual(portfolio.current_cash, self.initial_cash + pnl)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash + pnl)

        self.assertEqual(portfolio.gross_exposure_of_positions,
                         abs(quantity_after_second_transaction * self.point_value * new_price))
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_transact_transaction_split_and_close(self):
        portfolio, dh, _ = self.get_portfolio_and_data_handler()

        # Transact the initial transaction
        transactions = []
        quantity = 50

        # Set initial price for the given ticker
        self.data_handler_prices = self.prices_down
        price_1 = dh.get_last_available_price(self.fut_ticker)  # == 210

        initial_transaction = Transaction(self.random_time, self.fut_ticker, quantity=quantity, price=price_1,
                                          commission=10)
        portfolio.transact_transaction(initial_transaction)
        transactions.append(initial_transaction)
        portfolio.update()

        # Change of price for the given ticker
        self.data_handler_prices = self.prices_series
        price_2 = dh.get_last_available_price(self.fut_ticker)  # == 250

        transaction_to_split = Transaction(self.random_time, self.fut_ticker, quantity=(-2) * quantity,
                                           price=price_2, commission=18)
        portfolio.transact_transaction(transaction_to_split)
        transactions.append(transaction_to_split)
        portfolio.update()

        trade_pnl = (price_2 - price_1) * self.fut_ticker.point_value * quantity
        trade_pnl -= initial_transaction.commission
        trade_pnl -= transaction_to_split.commission * abs(initial_transaction.quantity / transaction_to_split.quantity)

        # Change of price for the given ticker
        self.data_handler_prices = self.prices_series
        price_3 = dh.get_last_available_price(self.fut_ticker)  # == 270
        closing_transaction = Transaction(self.random_time, self.fut_ticker, quantity=quantity,
                                          price=price_3, commission=5)
        portfolio.transact_transaction(closing_transaction)
        transactions.append(closing_transaction)
        portfolio.update()

        # All positions should be closed at this moment
        self.assertEqual(len(portfolio.open_positions_dict), 0)

    def test_portfolio_eod_series(self):
        expected_portfolio_eod_series = PricesSeries()

        # Empty portfolio
        portfolio, dh, timer = self.get_portfolio_and_data_handler()
        portfolio.update(record=True)
        expected_portfolio_eod_series[timer.time] = self.initial_cash

        # Buy contract
        self._shift_timer_to_next_day(timer)
        transaction_1 = Transaction(timer.time, self.fut_ticker, quantity=50, price=250, commission=7)
        portfolio.transact_transaction(transaction_1)
        self.data_handler_prices = self.prices_series
        portfolio.update(record=True)

        position = portfolio.open_positions_dict[self.fut_ticker]

        price_1 = dh.get_last_available_price(self.fut_ticker)
        pnl = self.fut_ticker.point_value * transaction_1.quantity * (price_1 - transaction_1.price)
        nav = self.initial_cash + pnl - transaction_1.commission
        expected_portfolio_eod_series[timer.time] = nav

        # Contract goes up in value
        self._shift_timer_to_next_day(timer)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        price_2 = dh.get_last_available_price(self.fut_ticker)  # == 270
        pnl = self.fut_ticker.point_value * transaction_1.quantity * (price_2 - price_1)
        nav += pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Sell part of the contract
        self._shift_timer_to_next_day(timer)
        transaction_2 = Transaction(timer.time, self.fut_ticker, quantity=-25, price=price_2, commission=19)
        portfolio.transact_transaction(transaction_2)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        pnl = (transaction_2.price - price_2) * transaction_2.quantity * self.fut_ticker.point_value - \
            transaction_2.commission
        nav += pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Price goes down
        self._shift_timer_to_next_day(timer)
        self.data_handler_prices = self.prices_down
        portfolio.update(record=True)

        price_3 = dh.get_last_available_price(self.fut_ticker)  # == 210
        pnl2 = self.fut_ticker.point_value * position.quantity() * (price_3 - price_2)
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
        position = None

        def record_leverage():
            expected_leverage_series[timer.now()] = position.total_exposure() / nav

        # Empty portfolio
        portfolio.update(record=True)
        expected_leverage_series[self.start_time] = 0

        # Buy contract
        self._shift_timer_to_next_day(timer)
        transaction_1 = Transaction(timer.now(), self.fut_ticker, quantity=50, price=250, commission=7)
        portfolio.transact_transaction(transaction_1)
        self.data_handler_prices = self.prices_series
        portfolio.update(record=True)

        position = portfolio.open_positions_dict[self.fut_ticker]

        # Compute the leverage
        pnl = self.fut_ticker.point_value * transaction_1.quantity * (position.current_price - transaction_1.price)
        nav += pnl - transaction_1.commission
        record_leverage()

        # Contract goes up in value
        self._shift_timer_to_next_day(timer)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        # Compute the leverage
        price_after_increase = position.current_price
        pnl = self.fut_ticker.point_value * transaction_1.quantity * (price_after_increase - transaction_1.price)
        nav = self.initial_cash + pnl - transaction_1.commission
        record_leverage()

        # Sell part of the contract
        self._shift_timer_to_next_day(timer)
        transaction_2 = Transaction(timer.time, self.fut_ticker, quantity=-30, price=position.current_price,
                                    commission=9)
        portfolio.transact_transaction(transaction_2)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        # Compute the leverage
        pnl = (transaction_2.price - price_after_increase) * transaction_2.quantity * self.fut_ticker.point_value
        nav += pnl - transaction_2.commission
        record_leverage()

        # Price goes down
        self._shift_timer_to_next_day(timer)
        self.data_handler_prices = self.prices_down
        portfolio.update(record=True)

        pnl = self.fut_ticker.point_value * position.quantity() * (position.current_price - transaction_2.price)
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

        portfolio.transact_transaction(Transaction(new_time, self.ticker, quantity, price, commission1))
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_series
        portfolio.update(record=True)

        gross_value = quantity * price
        pnl = quantity * (120 - 120)
        nav = self.initial_cash + pnl - commission1
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # contract goes up in value
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_up
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
        portfolio.transact_transaction(Transaction(new_time, self.ticker, quantity, price, commission2))
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        gross_value = 200 * 130
        nav = nav - commission2
        expected_values.append(gross_value / nav)
        expected_dates.append(new_time)

        # price goes down
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_down
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

        portfolio.transact_transaction(Transaction(new_time, self.fut_ticker, quantity, price, commission1))
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_series
        portfolio.update(record=True)

        # buy another instrument - price goes up
        portfolio.transact_transaction(Transaction(new_time, self.ticker, 20, 120, commission1))
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        # sell part of the contract
        quantity = -30
        price = 270
        commission2 = 9
        new_time = timer.time + RelativeDelta(days=1)
        portfolio.transact_transaction(Transaction(new_time, self.fut_ticker, quantity, price, commission2))
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_up
        portfolio.update(record=True)

        # price goes down
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)
        self.data_handler_prices = self.prices_down
        portfolio.update(record=True)

        asset_history = portfolio.positions_history()
        self.assertEqual(asset_history.shape, (5, 2))
        self.assertEqual(asset_history.iloc[4, 0].total_exposure, 315000)
        self.assertEqual(asset_history.iloc[4, 1].total_exposure, 2000)


if __name__ == "__main__":
    unittest.main()
