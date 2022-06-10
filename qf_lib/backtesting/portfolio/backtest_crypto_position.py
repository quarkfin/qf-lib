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
from numpy import sign
from math import isclose

from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.miscellaneous.constants import ISCLOSE_REL_TOL, ISCLOSE_ABS_TOL


class BacktestCryptoPosition(BacktestPosition):
    def market_value(self) -> float:
        return self.quantity() * self.current_price

    def total_exposure(self) -> float:
        return self._quantity * self.current_price

    def _cash_to_buy_or_proceeds_from_sale(self, transaction: Transaction) -> float:
        result = transaction.price * transaction.quantity + transaction.commission
        return -result

    def _compute_profit_and_loss_fraction(self, price: float, quantity: float):
        if sign(quantity) * self.direction() == -1:
            price_pnl = price - self._avg_price_per_unit
            # We multiply by the direction, so that the in case of finding a pair of transaction going in opposite
            # directions, the realized pnl of this operation would consider the direction of the position
            quantity = self.direction() * abs(quantity)
            return price_pnl * quantity
        else:
            return 0.0

    def transact_transaction(self, transaction: Transaction) -> float:
        self._check_if_open()
        assert transaction.ticker == self._ticker, "Ticker of the Transaction has to match the Ticker of the Position"
        assert isclose(transaction.quantity, 0, rel_tol=ISCLOSE_REL_TOL, abs_tol=ISCLOSE_ABS_TOL) is not True, "`Transaction.quantity` shouldn't be 0"
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

        if isclose(self._quantity + transaction.quantity, 0, rel_tol=ISCLOSE_REL_TOL, abs_tol=ISCLOSE_ABS_TOL):  # close the position if the number of shares drops to zero
            self._close_position(transaction.transaction_fill_time)

        self._quantity += transaction.quantity
        self._commission += transaction.commission

        return cash_move
