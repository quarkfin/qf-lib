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
from math import isclose
from typing import List, Sequence, Union, Optional

from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.backtesting.portfolio.utils import split_transaction_if_needed
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.constants import ISCLOSE_REL_TOL, ISCLOSE_ABS_TOL
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class TradesGenerator:
    """
    Class responsible for generating Trade objects from information provided in the form of Transactions or
    BacktestPositions.
    """

    def create_trades_from_backtest_positions(self, positions: Union[BacktestPosition, Sequence[BacktestPosition]],
                                              portfolio_values: Optional[QFSeries] = None) -> Union[Trade, Sequence[Trade]]:
        """
        Generates trades from BacktestPositions.

        Parameters
        ----------
        positions: BacktestPosition, Sequence[BacktestPosition]
            Position or positions that will be used to generated the trades
        portfolio_values: Optional[QFSeries]
            Series containing portfolio values at different point in time. It is optional and if provided, the
            percentage pnl value is set in the Trade.

        Returns
        --------
        Trade, Sequence[Trade]
            Generated Trade (in case of one BacktestPosition) or a sequence of Trades
        """
        positions, got_single_position = convert_to_list(positions, BacktestPosition)

        def compute_percentage_pnl(position: BacktestPosition):
            if portfolio_values is not None:
                return position.total_pnl / portfolio_values.asof(position.start_time)
            else:
                return None

        trades = [
            Trade(p.start_time, p.end_time, p.ticker(), p.total_pnl, p.total_commission(), p.direction(),
                  compute_percentage_pnl(p))
            for p in positions
        ]

        if got_single_position:
            return trades[0]
        else:
            return trades

    def create_trades_from_transactions(self, transactions: Sequence, portfolio_values: Optional[QFSeries] = None) \
            -> Sequence[Trade]:
        """
        Generates trades based on a series of Transactions.

        Parameters
        -----------
        transactions: Sequence
            Sequence of transactions, which should be parsed
        portfolio_values: Optional[QFSeries]
            Series containing portfolio values at different point in time. It is optional and if provided, the
            percentage pnl value is set in the Trade.

        Returns
        --------
        trades: Sequence[Trade]
            List containing trades information, sorted by the time of their creation
        """
        transactions_df = QFDataFrame.from_records(
            [(t, t.transaction_fill_time, t.ticker, t.quantity) for t in transactions],
            columns=["transaction", "time", "ticker", "quantity"])

        # Position size after transacting the transaction, where position is identified by "ticker" variable
        transactions_df.sort_values(by="time", inplace=True)
        transactions_df["position size"] = transactions_df.groupby(by="ticker")["quantity"].cumsum()

        # Assign position start values - a position was opened when the position size was equal to the quantity of
        # the transaction (the quantity of the ticker in the portfolio before transaction was = 0)
        new_positions_beginning = QFSeries([isclose(x, 0, rel_tol=ISCLOSE_REL_TOL, abs_tol=ISCLOSE_ABS_TOL) for x in transactions_df["position size"] - transactions_df["quantity"]])
        transactions_df.loc[:, "position start"] = None
        transactions_df.loc[new_positions_beginning, "position start"] = transactions_df.loc[new_positions_beginning].index
        transactions_df.loc[:, "position start"] = transactions_df.groupby(by="ticker")["position start"].apply(
            lambda tms: tms.fillna(method="ffill"))

        trades_series = transactions_df.groupby(by=["position start"])["transaction"].apply(
            lambda t: self._parse_position(t, portfolio_values))
        trades = trades_series.sort_index(level=1).tolist()

        return trades

    def _parse_position(self, transactions: QFSeries, portfolio_values: Optional[QFSeries]) -> QFSeries:
        """
        For the given position returns generated trades. Trade is defined as a transaction that goes in the direction of
        making your position smaller. For example selling part or entire long position is a trade, buying back part or
        entire short position is a trade, buying additional shares of existing long position is NOT a trade.

        Parameters
        ------------
        transactions: QFSeries
            Transactions belonging to one certain position.
        """

        transactions = self._split_transactions_if_needed(transactions)

        ticker = transactions[0].ticker  # type: Ticker
        backtest_positions = []

        backtest_position = BacktestPositionFactory.create_position(ticker)
        for transaction in transactions:
            backtest_position.transact_transaction(transaction)

            if backtest_position.is_closed():
                backtest_positions.append(backtest_position)
                backtest_position = BacktestPositionFactory.create_position(ticker)

        trades = self.create_trades_from_backtest_positions(backtest_positions, portfolio_values)

        return QFSeries(data=trades, index=[t.end_time for t in trades])

    def _split_transactions_if_needed(self, transactions_series: QFSeries):
        """
        Split these transactions, which change the direction of the position (e.g. the direction of the position
        """
        # before the transaction was -1, after it is 1)
        split_transactions = []  # type: List[Transaction]

        total_quantity: float = 0.0
        for transaction in transactions_series:
            split_required, closing_transaction, remaining_transaction = split_transaction_if_needed(total_quantity,
                                                                                                     transaction)
            total_quantity += transaction.quantity

            if split_required:
                split_transactions.extend([closing_transaction, remaining_transaction])
            else:
                split_transactions.append(transaction)

        return split_transactions
