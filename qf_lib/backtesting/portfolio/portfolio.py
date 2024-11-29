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
from datetime import datetime
from typing import List, Dict, Optional

from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition, BacktestPositionSummary
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.backtesting.portfolio.utils import split_transaction_if_needed
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.exchange_rate_provider import ExchangeRateProvider


class Portfolio:
    def __init__(self, data_provider: AbstractPriceDataProvider, initial_cash: float, currency: Optional[str] = None):
        """
        On creation, the Portfolio object contains no positions and all values are "reset" to the initial
        cash, with no PnL.
        """
        self.initial_cash = initial_cash
        self.data_provider = data_provider
        self.currency = currency

        self.net_liquidation = initial_cash
        """ Cash value includes futures P&L + stock value + securities options value + bond value + fund value. """

        self.gross_exposure_of_positions = 0
        """ Equals the sum of the absolute value of all positions except cash. """

        self.current_cash = initial_cash
        """ Represents the free cash in the portfolio. Part of the cash might be use for margin. """

        self.open_positions_dict = {}  # type: Dict[Ticker, BacktestPosition]
        """ Represents all open positions at a certain moment. """

        # dates and portfolio values are kept separately because it is inefficient to append to the QFSeries
        # use get_portfolio_timeseries() to get them as a series.
        self._dates = []  # type: List[datetime]
        self._portfolio_values = []  # type: List[float]
        self._leverage_list = []  # type: List[float]

        self._positions_history = []  # type: List[Dict[Ticker, BacktestPositionSummary]]
        """ A list containing dictionaries with summarized assets information in form of BacktestPositionSummary
        objects, which provide information about open positions at a certain point of time. """

        self._closed_positions = []  # type: List[BacktestPosition]
        """ List of all closed positions created throughout the backtest. """

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def _current_exchange_rate(self, currency: str) -> float:
        """Last available exchange rate from the specified currency to the portfolio currency."""
        if currency == self.currency:
            return 1.

        if isinstance(self.data_provider, ExchangeRateProvider):
            return self.data_provider.get_last_available_exchange_rate(currency, self.currency,
                                                                       frequency=self.data_provider.frequency)
        else:
            raise NotImplementedError(f"Portfolio currency is set to {self.currency} but {type(self.data_provider)} "
                                      "does not extend ExchangeRateProvider.")

    def net_liquidation_in_currency(self, currency: str = None) -> float:
        """Converts the current net liquidation from the portfolio currency into the specified currency"""
        if currency == self.currency:
            return self.net_liquidation
        elif self.currency is not None:
            return self.net_liquidation/self._current_exchange_rate(currency)
        else:
            raise ValueError("Portfolio currency is not specified.")

    def transact_transaction(self, transaction: Transaction):
        """
        Adjusts positions to account for a transaction.
        Handles any new position or modification to a current position
        """
        transaction_cost = 0.0

        existing_position = self.open_positions_dict.get(transaction.ticker, None)

        if existing_position is None:  # open new, empty position
            new_position = self._create_new_position(transaction)
            transaction_cost += new_position.transact_transaction(transaction)
        else:  # there is already an existing position
            results_in_opposite_direction, basic_transaction, remaining_transaction \
                = split_transaction_if_needed(existing_position.quantity(), transaction)

            transaction_cost += existing_position.transact_transaction(basic_transaction)
            if existing_position.is_closed():
                ticker = transaction.ticker
                self.open_positions_dict.pop(ticker)
                self._closed_positions.append(existing_position)

            if results_in_opposite_direction:  # means we were going from Long to Short in one transaction
                new_position = self._create_new_position(remaining_transaction)
                transaction_cost += new_position.transact_transaction(remaining_transaction)

        if self.currency is not None:
            self.current_cash += transaction_cost*self._current_exchange_rate(transaction.ticker.currency)
        else:
            self.current_cash += transaction_cost

    def update(self, record=False):
        """
        Updates the value of all positions that are currently open by getting the most recent price.
        The function is called at the end of the day (after market close) and after each executed transaction.
        If the flag record is set to True, it records the current assets values and the portfolio value (this is
        performed once per day, after the market close).
        """
        self.net_liquidation = self.current_cash
        self.gross_exposure_of_positions = 0

        tickers = list(self.open_positions_dict.keys())
        current_prices_series = self.data_provider.get_last_available_price(tickers=tickers)

        current_positions = {}
        for ticker, position in self.open_positions_dict.items():
            security_price = current_prices_series[ticker]
            position.update_price(bid_price=security_price, ask_price=security_price)
            position_value = position.market_value()
            position_exposure = position.total_exposure()

            current_exchange_rate = self._current_exchange_rate(ticker.currency) if self.currency is not None else 1.
            self.net_liquidation += position_value*current_exchange_rate
            self.gross_exposure_of_positions += abs(position_exposure)*current_exchange_rate

            if record:
                current_positions[ticker] = BacktestPositionSummary(position)

        if record:
            self._dates.append(self.data_provider.timer.now())
            self._portfolio_values.append(self.net_liquidation)
            self._leverage_list.append(self.gross_exposure_of_positions / self.net_liquidation)
            self._positions_history.append(current_positions)

    def portfolio_eod_series(self) -> PricesSeries:
        """
        Returns a timeseries of value of the portfolio expressed in currency units
        """
        end_of_day_date = list(map(lambda x: datetime(x.year, x.month, x.day), self._dates))  # remove time component
        portfolio_timeseries = PricesSeries(data=self._portfolio_values, index=end_of_day_date)
        return portfolio_timeseries

    def leverage_series(self) -> QFSeries:
        """
        Leverage = GrossPositionValue / NetLiquidation
        """
        return QFSeries(data=self._leverage_list, index=self._dates)  # type: QFSeries

    def positions_history(self) -> QFDataFrame:
        """
        Returns a QFDataFrame containing summary of the positions in the portfolio for each day.
        """
        return QFDataFrame(data=self._positions_history, index=self._dates)

    def closed_positions(self) -> List[BacktestPosition]:
        return self._closed_positions

    def _create_new_position(self, transaction: Transaction):
        new_position = BacktestPositionFactory.create_position(transaction.ticker)
        self.open_positions_dict[transaction.ticker] = new_position
        return new_position
