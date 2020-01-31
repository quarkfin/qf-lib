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

from numpy import sign

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.transaction import Transaction


class BacktestFuturePosition(BacktestPosition):
    def __init__(self, contract: Contract, start_time: datetime) -> None:
        super().__init__(contract, start_time)

    def market_value(self) -> float:
        """Market value is equal to the P&L of the position"""
        if self.current_price == 0:
            return 0.0

        multiplier = self._quantity * self._contract.contract_size
        price_pnl = self.current_price - self.avg_price_per_unit()
        return price_pnl * multiplier

    def total_exposure(self) -> float:
        return self._quantity * self._contract.contract_size * self.current_price

    def _cash_to_buy_or_proceeds_from_sale(self, transaction: Transaction) -> float:
        """
        To buy a future contract we only pay a commission.
        There is some cash secured as a margin but it is not leaving out portfolio
        """
        if (self.direction == 0) or (sign(transaction.quantity) == self.direction):
            # if first trade or trade in the direction of the position we only need to pay for commission
            return -transaction.commission
        else:
            # closing part of the position -> we need to cover the p&l of the position
            price_pnl = (transaction.price - self.avg_price_per_unit())
            multiplier = transaction.quantity * self._contract.contract_size

            # invert sign of multiplier because the sign of transaction.quantity
            # is opposite to the actual position.direction
            multiplier = -multiplier

            return price_pnl * multiplier - transaction.commission
