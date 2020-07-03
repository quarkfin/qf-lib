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
from typing import List, Optional

from numpy import sign

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.backtesting.portfolio.transaction import Transaction


class BacktestPosition(Position, metaclass=ABCMeta):
    def __init__(self, contract: Contract, start_time: datetime) -> None:
        self._contract = contract
        """Contract identifying the position"""

        self.is_closed = False
        """Determines if the positions has been closed"""

        self.transactions = []  # type: List[Transaction]
        """List of all transactions for the asset"""

        self._quantity = 0  # type: int
        """ Number of shares or contracts held currently in the portfolio. Positive value means this is a Long position
        Negative value corresponds to a Short position"""

        self.current_price = 0.0  # type: float
        """ Current price of the asset used for market value calculation. Includes the Bid-Ask spread"""

        self.direction = 0  # type: int
        """ Direction of the position: Long = 1, Short = -1, Not defined = 0"""

        self.start_time = start_time  # type: datetime
        """ Time of the position creation """

        self._remaining_total_commission_to_build_position = 0.0  # type: float
        self._avg_price_per_unit = 0.0

    @property
    def unrealised_pnl(self) -> float:
        """
        Unrealised profit or loss associated with a transcation expressed in currency units
        Does not include transaction costs and commissions
        """
        multiplier = self._quantity * self._contract.contract_size
        profit_loss = (self.current_price - self.avg_price_per_unit()) * multiplier
        return profit_loss

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
            It represents Notional of the position (quantity * price * contract_size)
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

    def avg_price_per_unit(self) -> float:
        """
        For the long position it tells us what was the average price paid to acquire one share of the position.
        For short positions it tells us what was the average value we received for one share of the position.
        return calculates share weighted average of the price without any transaction costs
        """
        if self._quantity == 0:
            return 0
        return self._avg_price_per_unit

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
        assert transaction.contract == self._contract, "Contract of Transaction has to match the Contract of a Position"
        assert transaction.quantity != 0, "`Transaction.quantity` shouldn't be 0"
        assert transaction.price > 0.0, "Transaction.price must be positive. For short sales use a negative quantity"
        sign_change = sign(self._quantity) * sign(self._quantity + transaction.quantity)
        assert sign_change != -1, "Position cannot change direction (for ex: from Long to Short). Close it first"

        # has to be called before we modify the quantity of the original position
        cash_move = self._cash_to_buy_or_proceeds_from_sale(transaction)

        # Adjust the remaining total commission to build the position
        is_a_trade = sign(transaction.quantity) * sign(self._quantity) == -1
        if not is_a_trade:
            self._remaining_total_commission_to_build_position += transaction.commission
            # Take weighted average of the previous average price per unit and transactions price per unit
            # Use position and transactions quantities as weights
            self._avg_price_per_unit = (self._avg_price_per_unit * self._quantity + transaction.price * transaction.quantity) / (self._quantity + transaction.quantity)
        else:
            fraction_of_position = min([abs(transaction.quantity), abs(self._quantity)]) / abs(self._quantity)
            self._remaining_total_commission_to_build_position *= (1 - fraction_of_position)

        self.transactions.append(transaction)
        self._quantity += transaction.quantity
        self.direction = sign(self._quantity)

        if self._quantity == 0:  # close the position if the number of shares drops to zero
            self.is_closed = True

        return cash_move

    def update_price(self, bid_price: float, ask_price: float):
        """
        Sets the current price of the security in a way that takes into account the bid-ask spread
        This is used for market valuation of the open position.
        This method should be called every time we have have a new price
        """
        self._check_if_open()

        if self._quantity > 0:  # we are long -> use the lower (bid) price
            self.current_price = bid_price
        elif self._quantity < 0:  # we are short -> use the higher (ask) price
            self.current_price = ask_price

    def contract(self) -> Contract:
        return self._contract

    def quantity(self) -> int:
        return self._quantity

    def remaining_total_commission(self) -> float:
        return self._remaining_total_commission_to_build_position

    def _check_if_open(self):
        assert not self.is_closed, "The position has already been closed"

    def check_if_transaction_generates_trade(self, transaction: Transaction) -> Optional[Trade]:
        """
        In case if the given transaction would result in a trade, the potential trade is returned.
        In other case the function returns None.

        Trade is defined as a transaction that goes in the direction of making your position smaller.
        For example selling part or entire long position is a trade, buying back part or entire short position is a
        trade, buying additional shares of existing long position is NOT a trade


        """
        total_quantity = self._quantity

        is_a_trade = sign(transaction.quantity) * sign(total_quantity) == -1
        if not is_a_trade:
            return None

        # Compute the fraction of the total position before the last transaction (only the part that goes in the
        # opposite direction is considered as a trade)
        quantity = min([abs(transaction.quantity), abs(total_quantity)])
        quantity *= sign(total_quantity)

        # commission = fraction of the remaining commission (before transaction) to build the position + 100% of the
        # cost to reduce the position
        fraction_of_position = quantity / total_quantity
        commission = self._remaining_total_commission_to_build_position * fraction_of_position
        commission += transaction.commission

        trade = Trade(start_time=self.start_time,
                      end_time=transaction.time,
                      contract=transaction.contract,
                      quantity=quantity,
                      entry_price=self.avg_price_per_unit(),
                      exit_price=transaction.price,
                      commission=commission)
        return trade
