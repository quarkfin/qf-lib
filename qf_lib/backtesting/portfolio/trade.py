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

from qf_lib.backtesting.contract.contract import Contract


class Trade(object):
    """
    Trade represents a pair of transactions that go in the opposite directions.
    For example:
        We buy 10 shares of X and then we sell 3 shares of X. This creates a trade when we buy and sell 3 shares of X
    """

    def __init__(self, time: datetime, contract: Contract, quantity: int, entry_price: float, exit_price: float,
                 risk_as_percent: float = float('nan')):
        """
        time
            moment when we close the trade
        contract
            contract defining the security
        quantity
            number of shares traded
        entry_price
            price at which the instrument has been bought including transaction costs
        exit_price
            price at which the trade was closed including all fees and commission
        risk_as_percent
            max percentage risk that we aim to have on this instrument.
            for example it could be the the percentage that is used to calculate the stop price.
        """
        self.time = time
        self.contract = contract
        self.quantity = quantity
        self.entry_price = entry_price
        self.exit_price = exit_price

        self.risk_as_percent = risk_as_percent

    def define_risk(self, risk_as_percent: float):
        """
        If not known up front (in the constructor), the risk percentage can be defined later on.
        """
        self.risk_as_percent = risk_as_percent

    @property
    def pnl(self) -> float:
        """
        Profit or loss associated with a trade expressed in currency units
        including transaction costs and commissions
        """
        profit_loss = (self.exit_price - self.entry_price) * self.quantity
        return profit_loss

    @property
    def total_risk(self) -> float:
        """
        total risk associated with a trade expressed in currency units.
        It is the maximum loss that we expect to get while holding 'self.quantity' units of 'self.contract'
        """
        total_risk = abs(self.entry_price * self.risk_as_percent * self.quantity)
        return total_risk

    @property
    def r_multiply(self) -> float:
        """
        R multiply is the ratio of (profit or loss) to (total risk)
        """
        result = self.pnl / self.total_risk
        return result
