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

import copy
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import numpy as np
from numpy import sign

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
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
        self.gross_exposure_of_positions = 0

        """represents the free cash in the portfolio. Part of the cash might be use for margin"""
        self.current_cash = initial_cash

        """represents all open positions at the moment"""
        self.open_positions_dict = {}  # type: Dict[Contract, BacktestPosition]

        # dates and portfolio values are keep separately because it is inefficient to append to the QFSeries
        # use get_portfolio_timeseries() to get them as a series.
        self._dates = []  # type: List[datetime]
        self._portfolio_values = []  # type: List[float]
        self._leverage_list = []  # type: List[float]
        self._transactions = []  # type: List[Transaction]
        self._trades = []  # type: List[Trade]

        # A list containing dictionaries with summarized assets information (contains a mapping from
        # contracts to market value at the specific time)
        self.positions_history = []

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def transact_transaction(self, transaction: Transaction):
        """
        Adjusts positions to account for a transaction.
        Handles any new position or modification to a current position
        """
        self._transactions.append(transaction)
        transaction_cost = 0.0

        existing_position = self.open_positions_dict.get(transaction.contract, None)

        if existing_position is None:  # open new, empty position
            new_position = self._create_new_position(transaction)
            transaction_cost += new_position.transact_transaction(transaction)
        else:  # there is already an existing position
            self._record_potential_trade(existing_position, transaction)

            results_in_opposite_direction, basic_transaction, remaining_transaction \
                = self._split_if_results_in_opposite_direction(existing_position, transaction)

            transaction_cost += existing_position.transact_transaction(basic_transaction)

            if existing_position.is_closed:
                self.open_positions_dict.pop(transaction.contract)

            if results_in_opposite_direction:  # means we were going from Long to Short in one transaction
                new_position = self._create_new_position(remaining_transaction)
                transaction_cost += new_position.transact_transaction(remaining_transaction)

        self.current_cash += transaction_cost

    def update(self, record=False):
        """
        Updates the value of all positions that are currently open by getting the most recent price.
        The function is called at the end of the day (after market close) and after each executed trade.
        If the flag record is set to True, it records the current assets values and the portfolio value (this is
        performed once per day, after the market close).
        """
        self.net_liquidation = self.current_cash
        self.gross_exposure_of_positions = 0

        contracts = self.open_positions_dict.keys()
        contract_to_ticker_dict = {
            contract: self.contract_ticker_mapper.contract_to_ticker(contract) for contract in contracts}

        all_tickers_in_portfolio = list(contract_to_ticker_dict.values())
        current_prices_series = self.data_handler.get_last_available_price(tickers=all_tickers_in_portfolio)

        self._remove_positions_acquired_or_not_active_positions(contract_to_ticker_dict, current_prices_series)

        current_positions = {}
        for contract, position in self.open_positions_dict.items():
            ticker = contract_to_ticker_dict[contract]
            security_price = current_prices_series[ticker]
            position.update_price(bid_price=security_price, ask_price=security_price)
            position_value = position.market_value()
            position_exposure = position.total_exposure()
            self.net_liquidation += position_value
            self.gross_exposure_of_positions += abs(position_exposure)
            if record:
                current_positions[contract] = position_exposure

        if record:
            self._dates.append(self.timer.now())
            self._portfolio_values.append(self.net_liquidation)
            self._leverage_list.append(self.gross_exposure_of_positions / self.net_liquidation)
            self.positions_history.append(current_positions)

    def _remove_positions_acquired_or_not_active_positions(self, contract_to_ticker_dict, current_prices_series):
        contracts_to_be_removed = [c for c in self.open_positions_dict
                                   if np.isnan(current_prices_series[contract_to_ticker_dict[c]])]
        for contract in contracts_to_be_removed:
            position = self.open_positions_dict.pop(contract)
            self.current_cash += position.market_value()
            self.net_liquidation += position.market_value()
            self.logger.warning("{}: position assigned to Ticker {} removed due to incomplete price data."
                                .format(str(self.timer.now()), contract.symbol))

    def portfolio_eod_series(self) -> PricesSeries:
        """
        Returns a timeseries of value of the portfolio expressed in currency units
        """
        end_of_day_date = list(map(lambda x: datetime(x.year, x.month, x.day), self._dates))  # remove time component
        portfolio_timeseries = PricesSeries(data=self._portfolio_values, index=end_of_day_date)
        return portfolio_timeseries

    def trade_list(self) -> List[Trade]:
        """
        Returns a list of Trades
        """
        return self._trades

    def leverage_series(self) -> QFSeries:
        """
        Leverage = GrossPositionValue / NetLiquidation
        """
        return QFSeries(data=self._leverage_list, index=self._dates)  # type: QFSeries

    def positions_eod_history(self) -> QFDataFrame:
        """
        Returns a QFDataFrame containing exposure of the positions in the portfolio for each day.
        each day contains a dict [contract -> exposure]
        """
        end_of_day_date = list(map(lambda x: datetime(x.year, x.month, x.day), self._dates))  # remove time component
        return QFDataFrame(data=self.positions_history, index=end_of_day_date)

    def transactions_series(self) -> QFSeries:
        """
        Returns a time series of transactions. It will have multiple entries with the same value of the
        index in more then one transaction occurred on the same day
        """
        time_index = (t.time for t in self._transactions)
        return QFSeries(data=self._transactions, index=time_index)

    @staticmethod
    def _split_if_results_in_opposite_direction(existing_position: BacktestPosition, transaction: Transaction) \
            -> Tuple[bool, Transaction, Optional[Transaction]]:

        existing_quantity = existing_position.quantity()
        sign_before = sign(existing_quantity)
        sign_after = sign(existing_quantity + transaction.quantity)

        if sign_before * sign_after == -1:
            # split transaction into two transactions
            # 1. close existing position
            # 2. open new position with the remaining part
            closing_quantity = -existing_quantity

            closing_transaction = copy.deepcopy(transaction)
            closing_transaction.quantity = closing_quantity
            closing_transaction.commission = transaction.commission * (closing_quantity / transaction.quantity)

            remaining_quantity = transaction.quantity - closing_quantity
            remaining_transaction = copy.deepcopy(transaction)
            remaining_transaction.quantity = remaining_quantity
            remaining_transaction.commission = transaction.commission * (remaining_quantity / transaction.quantity)
            return True, closing_transaction, remaining_transaction

        return False, transaction, None

    def _record_potential_trade(self, existing_position: BacktestPosition, transaction: Transaction):
        """
        existing_position
            is a position that we held in the portfolio, before the transaction was booked
        transaction
            describes how we change the existing position

        Trade is defined as a transaction that goes in the direction of making your position smaller.
        For example:
           selling part or entire long position is a trade
           buying back part or entire short position is a trade
           buying additional shares of existing long position is NOT a trade
        """
        existing_quantity = existing_position.quantity()
        is_a_trade = sign(transaction.quantity) * sign(existing_quantity) == -1
        if is_a_trade:
            # only the part that goes in the opposite direction is considered as a trade
            quantity = min([abs(transaction.quantity), abs(existing_quantity)])
            quantity *= sign(existing_quantity)  # sign of the position should be preserved

            # commission = fraction of the commission to build the position + 100% of the cost to reduce the position
            fraction_of_positon = quantity / existing_position.quantity()
            commission = existing_position.total_commission_to_build_position() * fraction_of_positon
            commission += transaction.commission

            trade = Trade(start_time=existing_position.start_time,
                          end_time=transaction.time,
                          contract=transaction.contract,
                          quantity=quantity,
                          entry_price=existing_position.avg_price_per_unit(),
                          exit_price=transaction.price,
                          commission=commission)
            self._trades.append(trade)

    def _create_new_position(self, transaction: Transaction):
        new_position = BacktestPositionFactory.create_position(transaction.contract, transaction.time)
        self.open_positions_dict[transaction.contract] = new_position
        return new_position


