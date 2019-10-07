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
from typing import List, Dict

import numpy as np
from numpy import sign

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class Portfolio(object):
    def __init__(self, data_handler: DataHandler, initial_cash: float, timer: Timer,
                 contract_ticker_mapper: ContractTickerMapper):
        """
        On creation, the Portfolio object contains no positions and all values are "reset" to the initial
        cash, with no PnL.
        """
        self.initial_cash = initial_cash
        self.data_handler = data_handler
        self.timer = timer
        self.contract_ticker_mapper = contract_ticker_mapper

        """cash value includes futures P&L + stock value + securities options value + bond value + fund value."""
        self.net_liquidation = initial_cash

        """equals the sum of the absolute value of all positions except cash """
        self.gross_value_of_positions = 0

        # dates and portfolio values are keep separately because it is inefficient to append to the QFSeries
        # use get_portfolio_timeseries() to get them as a series.
        self.dates = []  # type: List[datetime]
        self.portfolio_values = []  # type: List[float]
        self.current_cash = initial_cash

        self._leverage = []  # type: List[float]

        self.open_positions_dict = {}  # type: Dict[Contract, BacktestPosition]
        self.transactions = []  # type: List[Transaction]
        self.trades = []  # type: List[Trade]

        # A list containing dictionaries with summarized assets information (contains a mapping from
        # contracts to market value at the specific time)
        self._assets_history = []

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def transact_transaction(self, transaction: Transaction):
        """
        Adjusts positions to account for a transaction.
        Handles any new position or modification to a current position
        """

        position = self._get_or_create_position(transaction.contract)
        prev_position_quantity = position.quantity()
        prev_position_avg_price = position.avg_cost_per_share()
        transaction_cost = position.transact_transaction(transaction)
        self.current_cash -= transaction_cost

        self._record_trade_and_transaction(prev_position_quantity, prev_position_avg_price, transaction)

        # if the position was closed: remove it from open positions and place in closed positions
        if position.is_closed:
            self.open_positions_dict.pop(transaction.contract)

    def update(self):
        """
        Updates the value of all positions that are currently open by getting the most recent price.
        """
        self.net_liquidation = self.current_cash
        self.gross_value_of_positions = 0

        contracts = self.open_positions_dict.keys()
        contract_to_ticker_dict = {
            contract: self.contract_ticker_mapper.contract_to_ticker(contract) for contract in contracts}

        all_tickers_in_portfolio = list(contract_to_ticker_dict.values())
        current_prices_series = self.data_handler.get_last_available_price(tickers=all_tickers_in_portfolio)

        self._remove_positions_assigned_to_acquired_companies(contract_to_ticker_dict, current_prices_series)

        current_assets = {}
        for contract, position in self.open_positions_dict.items():
            ticker = contract_to_ticker_dict[contract]
            security_price = current_prices_series[ticker]
            position.update_price(bid_price=security_price, ask_price=security_price)
            self.net_liquidation += position.market_value
            self.gross_value_of_positions += abs(position.market_value)
            current_assets[contract] = position.market_value

        self.dates.append(self.timer.now())
        self.portfolio_values.append(self.net_liquidation)
        self._leverage.append(self.gross_value_of_positions / self.net_liquidation)
        self._assets_history.append(current_assets)

    def _remove_positions_assigned_to_acquired_companies(self, contract_to_ticker_dict, current_prices_series):
        remove = [c for c in self.open_positions_dict if np.isnan(current_prices_series[contract_to_ticker_dict[c]])]
        for con in remove:
            pos = self.open_positions_dict[con]
            self.current_cash += pos.current_price * pos.number_of_shares
            self.net_liquidation += pos.current_price * pos.number_of_shares
            del self.open_positions_dict[con]
            self.logger.warning("{}: position assigned to Ticker {} removed due to incomplete price data."
                                .format(str(self.timer.now()), con.symbol))

    def get_portfolio_eod_tms(self) -> PricesSeries:
        """
        Returns a timeseries of value of the portfolio expressed in currency units
        """
        end_of_day_date = list(map(lambda x: datetime(x.year, x.month, x.day), self.dates))  # remove the time component
        portfolio_timeseries = PricesSeries(data=self.portfolio_values, index=end_of_day_date)
        return portfolio_timeseries

    def get_trades(self) -> List[Trade]:
        """
        Returns a list of Trades
        """
        return self.trades

    def leverage(self) -> QFSeries:
        """
        Leverage = GrossPositionValue / NetLiquidation
        """
        return QFSeries(data=self._leverage, index=self.dates)

    def _get_or_create_position(self, contract: Contract) -> BacktestPosition:
        position = self.open_positions_dict.get(contract, None)
        if position is None:
            position = BacktestPosition(contract)
            self.open_positions_dict[contract] = position

        return position

    def _record_trade_and_transaction(
            self, prev_position_quantity: int, prev_position_avg_price: float, transaction: Transaction):
        """
        Trade is defined as a transaction that goes in the direction of making your position smaller.
        For example:
           selling part or entire long position is a trade
           buying back part or entire short position is a trade
           buying additional shares of existing long position is NOT a trade
        """
        self.transactions.append(transaction)

        is_a_trade = sign(transaction.quantity) * sign(prev_position_quantity) == -1
        if is_a_trade:
            time = transaction.time
            contract = transaction.contract

            # only the part that goes in the opposite direction is considered as a trade
            quantity = min([abs(transaction.quantity), abs(prev_position_quantity)])
            quantity *= sign(prev_position_quantity)  # sign of the position should be preserved

            entry_price = prev_position_avg_price
            exit_price = transaction.average_price_including_commission()
            trade = Trade(time=time,
                          contract=contract,
                          quantity=quantity,
                          entry_price=entry_price,
                          exit_price=exit_price)
            self.trades.append(trade)

    def assets_history(self) -> QFDataFrame:
        """
        Returns a QFDataFrame containing the number of assets in the portfolio for each of the dates.
        """
        return QFDataFrame(data=self._assets_history, index=self.dates)

    def transactions_series(self) -> QFSeries:
        time_index = (t.time for t in self.transactions)
        return QFSeries(data=self.transactions, index=time_index)
