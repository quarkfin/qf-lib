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
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Optional

from numpy import sign

from qf_lib.backtesting.portfolio.position import Position
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


class BacktestPosition(Position, metaclass=ABCMeta):
    def __init__(self, ticker: Ticker) -> None:
        self._ticker = ticker
        """ Ticker identifying the position. """

        self._current_price = None  # type: Optional[float]
        """ Current price of the asset used for market value calculation. Includes the Bid-Ask spread. """

        self.start_time = None  # type: Optional[datetime]
        """ Time of the position creation. """

        self.end_time = None  # type: Optional[datetime]
        """ Time of the position closing (None in case if the position is still open). """

        self._direction = 0  # type: int
        """ Direction of the position: Long = 1, Short = -1, Not defined = 0.0."""

        self._is_closed = False
        """ Determines if the position has been closed. """

        self._realised_pnl_without_commissions = 0.0  # type: float
        """ Total realised pnl, excluding commissions. """

        self._avg_price_per_unit = 0.0  # type: float
        """ For the long position it tells us what was the average price paid to acquire one share of the position.
        For short positions it tells us what was the average value we received for one share of the position.
        return calculates share weighted average of the price without any transaction costs. """

        self._quantity = 0
        """ Quantity of the position. """

        self._commission = 0
        """ Sum of the commissions of all transacted transactions. """

    @property
    def current_price(self) -> float:
        if self._current_price is None:
            return 0.0
        return self._current_price

    @property
    def unrealised_pnl(self) -> float:
        """
        Unrealised profit or loss associated with a transaction expressed in currency units
        Does not include transaction costs and commissions
        """
        if self._current_price is None:
            return 0.0

        profit_loss = self._compute_profit_and_loss_fraction(self.current_price, - self.quantity())
        return profit_loss

    @property
    def total_pnl(self):
        """ Total pnl including all commissions and fees. """
        return self._realised_pnl_without_commissions + self.unrealised_pnl - self.total_commission()

    @abstractmethod
    def market_value(self) -> float:
        """
        It tells us what is the Market Value of the position.

        For cash securities (Equities, Bonds, ETFs, etc)
            It represents the value of the position (quantity * price) which is equal to the amount we could receive
            when we close the position

        For margin securities (Futures, Options)
            It represents the P&L of the position. So right after we buy a future contract its market_value is 0.
            It also represents the cash we could receive when we liquidate the position

        Different behaviour comes form the fact that when we buy cash security we need to spend cash
            (cash is removed from the portfolio)
        However, when we buy a margin instrument (for example future contract) our cash is intact,
            we only secure the margin which is not deducted from the cash we have.
        """
        pass

    @abstractmethod
    def total_exposure(self) -> float:
        """
        It tells us what is the total exposure of the position to the market in currency units

        For cash securities (Equities, Bonds, ETFs, etc)
            It represents the value of the position (quantity * price)

        For margin securities (Futures, Options)
            It represents Notional of the position (quantity * price * contract size)
        """
        pass

    @abstractmethod
    def _cash_to_buy_or_proceeds_from_sale(self, transaction: Transaction) -> float:
        """
        Calculates how much we paid to buy assets or how much we received for selling assets (including commission)

        For BUY transaction: how much we paid for the transaction including commission (it will be a negative number)
        For SELL transaction: how much we received for selling shares including commission
                             (it will be a positive number)
        """
        pass

    def transact_transaction(self, transaction: Transaction) -> float:
        """
        Update the state of a Position by using the Transaction containing information about datetime, price,
        quantity and commission.

        Returns
        -------
        transaction cost
        For BUY transaction: how much we paid for the transaction including commission (it will be a negative number)
        For SELL transaction: how much we received for selling shares including commission
                             (it will be a positive number)
        """
        self._check_if_open()
        assert transaction.ticker == self._ticker, "Ticker of the Transaction has to match the Ticker of the Position"
        assert transaction.quantity != 0, "`Transaction.quantity` shouldn't be 0"
        assert transaction.price > 0.0, "Transaction.price must be positive. For short sales use a negative quantity"

        if self.start_time is None:
            self.start_time = transaction.transaction_fill_time

        if self._direction == 0:
            self._direction = sign(transaction.quantity)

        sign_change = sign(self._quantity) * sign(self._quantity + transaction.quantity)
        assert sign_change != -1, "Position cannot change direction (for ex: from Long to Short). Close it first"

        # has to be called before we append the transaction to list of all transactions
        cash_move = self._cash_to_buy_or_proceeds_from_sale(transaction)
        self._realised_pnl_without_commissions += self._compute_profit_and_loss_fraction(price=transaction.price,
                                                                                         quantity=transaction.quantity)

        if sign(transaction.quantity) == self.direction():
            self._avg_price_per_unit = (self._avg_price_per_unit * self._quantity + transaction.price *
                                        transaction.quantity) / (self._quantity + transaction.quantity)

        if self._quantity + transaction.quantity == 0:  # close the position if the number of shares drops to zero
            self._close_position(transaction.transaction_fill_time)

        self._quantity += transaction.quantity
        self._commission += transaction.commission

        return cash_move

    def update_price(self, bid_price: float, ask_price: float):
        """
        Sets the current price of the security in a way that takes into account the bid-ask spread
        This is used for market valuation of the open position.
        This method should be called every time we have have a new price
        """
        self._check_if_open()
        if self._quantity > 0 and is_finite_number(bid_price):  # we are long -> use the lower (bid) price
            self._current_price = bid_price
        elif self._quantity < 0 and is_finite_number(ask_price):  # we are short -> use the higher (ask) price
            self._current_price = ask_price

    def direction(self) -> int:
        return self._direction

    def ticker(self) -> Ticker:
        return self._ticker

    def quantity(self) -> int:
        """ Number of shares or contracts held currently in the portfolio. Positive value means this is a Long position
        Negative value corresponds to a Short position. """
        return self._quantity

    def total_commission(self) -> float:
        """ Sum of all commissions of transactions. """
        return self._commission

    def is_closed(self):
        return self._is_closed

    def _close_position(self, time: datetime):
        self._is_closed = True
        self.end_time = time

    def _check_if_open(self):
        assert not self._is_closed, "The position has already been closed"

    @abstractmethod
    def _compute_profit_and_loss_fraction(self, price: float, quantity: int):
        """
        For the given backtest position state, computes what will be the pnl of a new transaction, defined by the
        given price and quantity. Returns 0.0 if the transaction is in the same direction as the position direction,
        and potential realized profit and loss in case of transaction in the opposite direction.
        """
        pass


class BacktestPositionSummary:
    def __init__(self, backtest_position: BacktestPosition):
        self.ticker = backtest_position.ticker()
        self.total_exposure = backtest_position.total_exposure()
        self.market_values = backtest_position.market_value()
        self.total_pnl = backtest_position.total_pnl
        self.direction = backtest_position.direction()
