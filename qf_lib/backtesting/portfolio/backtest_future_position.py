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

from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.transaction import Transaction


class BacktestFuturePosition(BacktestPosition):
    def market_value(self) -> float:
        """Market value is equal to the P&L of the position"""
        return self.unrealised_pnl

    def total_exposure(self) -> float:
        """
        It tells us what is the total exposure of the position to the market in currency units

        For cash securities (Equities, Bonds, ETFs, etc)
            It represents the value of the position (quantity * price)

        For margin securities (Futures, Options)
            It represents Notional of the position (quantity * price * contract_size)
        """
        return self._quantity * self._ticker.point_value * self.current_price

    def _cash_to_buy_or_proceeds_from_sale(self, transaction: Transaction) -> float:
        """
        To buy a future contract we only pay a commission. There is some cash secured as a margin but it is not leaving
        out portfolio.

        Therefore, if the transaction is the first transaction or made in the direction of the position we only need to
        pay for commission. In case of a transaction in the opposite direction to the position, we need to cover also
        the profit and loss of the trade.
        """
        transaction_pnl = self._compute_profit_and_loss_fraction(transaction.price, transaction.quantity)
        return transaction_pnl - transaction.commission

    def _compute_profit_and_loss_fraction(self, price: float, quantity: int):
        if sign(quantity) * self.direction() == -1:
            price_pnl = price - self._avg_price_per_unit
            # We multiply by the direction, so that the in case of finding a pair of transaction going in opposite
            # directions, the realized pnl of this operation would consider the direction of the position
            quantity = self.direction() * abs(quantity)
            multiplier = quantity * self._ticker.point_value
            return price_pnl * multiplier
        else:
            return 0.0
