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
from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg.bloomberg_data_provider import BloombergDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestPortfolioWithCurrency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.initial_cash = 1000000  # 1M
        cls.currency = "CHF"

        cls.usd_ticker = BloombergTicker('AAPL US Equity', SecurityType.STOCK, currency="USD")
        cls.chf_ticker = BloombergTicker('ZURN SW Equity', SecurityType.STOCK, currency="CHF")
        cls.point_value = 75
        cls.fut_ticker = BloombergTicker('CTZ9 Comdty', SecurityType.FUTURE, cls.point_value, "USD")
        cls.currency_ticker = BloombergTicker('USDCHF', SecurityType.FX)

        tickers = [cls.usd_ticker, cls.chf_ticker, cls.fut_ticker, cls.currency_ticker]
        cls.prices_series = QFSeries(data=[120, 56, 250, 0.95], index=tickers)
        cls.prices_up = QFSeries(data=[130, 65, 270, 0.98], index=tickers)
        cls.prices_down = QFSeries(data=[100, 49, 210, 0.98], index=tickers)

        cls.start_time = str_to_date('2017-01-01')
        cls.end_time = str_to_date('2017-02-02')
        cls.trades_generator = TradesGenerator()

    def setUp(self) -> None:
        self.data_provider_prices = None

    def get_portfolio_and_data_provider(self):
        data_provider = Mock(spec=BloombergDataProvider)
        data_provider.frequency = Frequency.DAILY
        data_provider.get_last_available_price.side_effect = lambda tickers: self.data_provider_prices[tickers] \
            if tickers else None
        data_provider.get_last_available_exchange_rate.side_effect = \
            lambda base_currency, quote_currency, frequency: self.data_provider_prices[BloombergTicker(
                f'{base_currency}{quote_currency}', SecurityType.FX)]

        timer = SettableTimer()
        timer.set_current_time(self.start_time)
        data_provider.timer = timer

        portfolio = Portfolio(data_provider, self.initial_cash, currency=self.currency)
        return portfolio, data_provider, timer

    @staticmethod
    def _shift_timer_to_next_day(timer: SettableTimer):
        new_time = timer.time + RelativeDelta(days=1)
        timer.set_current_time(new_time)

    @staticmethod
    def _cash_move(transaction: Transaction):
        return -1 * transaction.price * transaction.quantity * transaction.ticker.point_value - transaction.commission

    def test_transact_transaction_1(self):
        portfolio, data_provider, _ = self.get_portfolio_and_data_provider()

        self.data_provider_prices = self.prices_series

        transaction = Transaction(self.end_time, self.usd_ticker, quantity=50, price=100, commission=5, )
        portfolio.transact_transaction(transaction)

        cash_move_1 = self._cash_move(transaction)
        cash_move_1 *= data_provider.get_last_available_exchange_rate(self.usd_ticker.currency, self.currency, Frequency.DAILY)

        self.assertEqual(portfolio.initial_cash, self.initial_cash)
        self.assertEqual(portfolio.net_liquidation, self.initial_cash)
        self.assertEqual(portfolio.gross_exposure_of_positions, 0)  # not yet updated
        self.assertEqual(portfolio.current_cash, self.initial_cash + cash_move_1)
        self.assertEqual(len(portfolio.open_positions_dict), 1)

    def test_net_liquidation_in_currency(self):

        portfolio, _, _ = self.get_portfolio_and_data_provider()
        portfolio.update(record=True)
        self.data_provider_prices = self.prices_series

        portfolio_value_USD = portfolio.net_liquidation_in_currency(currency="USD")
        portfolio_value_CHF = portfolio.net_liquidation_in_currency(currency="CHF")

        assert portfolio_value_USD == self.initial_cash / self.prices_series.loc[self.currency_ticker]
        assert portfolio_value_CHF == self.initial_cash

    def test_net_liquidation_no_currency(self):

        portfolio, _, _ = self.get_portfolio_and_data_provider()
        portfolio.update(record=True)
        portfolio.currency = None
        self.data_provider_prices = self.prices_series

        with self.assertRaises(ValueError):
            portfolio.net_liquidation_in_currency(currency="USD")

    def test_portfolio_eod_series(self):
        expected_portfolio_eod_series = PricesSeries()

        # Empty portfolio
        portfolio, data_provider, timer = self.get_portfolio_and_data_provider()
        portfolio.update(record=True)
        expected_portfolio_eod_series[timer.time] = self.initial_cash

        self.data_provider_prices = self.prices_series

        # Buy contract
        self._shift_timer_to_next_day(timer)
        transaction_1 = Transaction(timer.time, self.fut_ticker, quantity=50, price=250, commission=7)
        portfolio.transact_transaction(transaction_1)
        portfolio.update(record=True)

        price_1 = data_provider.get_last_available_price(self.fut_ticker)
        pnl = self.fut_ticker.point_value * transaction_1.quantity * (price_1 - transaction_1.price) - transaction_1.commission
        pnl *= data_provider.get_last_available_exchange_rate(self.fut_ticker.currency, self.currency, Frequency.DAILY)
        nav = self.initial_cash + pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Contract goes up in value
        self._shift_timer_to_next_day(timer)
        self.data_provider_prices = self.prices_up
        portfolio.update(record=True)

        price_2 = data_provider.get_last_available_price(self.fut_ticker)  # == 270
        pnl = self.fut_ticker.point_value * transaction_1.quantity * (price_2 - price_1)
        pnl *= data_provider.get_last_available_exchange_rate(self.fut_ticker.currency, self.currency, Frequency.DAILY)
        nav += pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Sell part of the contract
        self._shift_timer_to_next_day(timer)
        self.data_provider_prices = self.prices_up
        transaction_2 = Transaction(timer.time, self.fut_ticker, quantity=-25, price=price_2, commission=19)
        portfolio.transact_transaction(transaction_2)
        portfolio.update(record=True)

        pnl = (transaction_2.price - price_2) * transaction_2.quantity * self.fut_ticker.point_value - \
            transaction_2.commission
        pnl *= data_provider.get_last_available_exchange_rate(self.fut_ticker.currency, self.currency, Frequency.DAILY)
        nav += pnl
        expected_portfolio_eod_series[timer.time] = nav

        # Price goes down
        self._shift_timer_to_next_day(timer)
        self.data_provider_prices = self.prices_down
        portfolio.update(record=True)

        position = portfolio.open_positions_dict[self.fut_ticker]

        price_3 = data_provider.get_last_available_price(self.fut_ticker)  # == 210
        pnl2 = self.fut_ticker.point_value * position.quantity() * (price_3 - price_2)
        pnl2 *= data_provider.get_last_available_exchange_rate(self.fut_ticker.currency, self.currency, Frequency.DAILY)
        nav += pnl2
        expected_portfolio_eod_series[timer.time] = nav

        tms = portfolio.portfolio_eod_series()
        assert_series_equal(expected_portfolio_eod_series, tms)

    def test_assert_data_provider_without_currency_raises_error(self):
        data_provider = Mock(spec=AbstractPriceDataProvider)
        portfolio = Portfolio(data_provider, self.initial_cash, currency=self.currency)
        self.data_provider_prices = self.prices_series
        transaction = Transaction(self.end_time, self.usd_ticker, quantity=50, price=100, commission=5, )
        with self.assertRaises(NotImplementedError):
            portfolio.transact_transaction(transaction)
