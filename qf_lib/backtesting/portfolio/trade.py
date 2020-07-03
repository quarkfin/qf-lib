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
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class Trade(object):
    """
    Trade represents a pair of transactions that go in the opposite directions.
    For example we buy 10 shares of X and then we sell 3 shares of X. This creates a trade when we buy and sell 3
    shares of X

    Parameters
    -----------
    start_time: datetime
        moment when we opened the position corresponding to this trade
    end_time: datetime
        moment when we close the trade
    contract: Contract
        contract defining the security
    quantity: int
        number of shares traded
    entry_price: float
        price at which the instrument has been bought (excluding all fees and commission)
    exit_price: float
        price at which the trade was closed (excluding all fees and commission)
    commission: float
        all the transaction costs related to the trade.
        It includes the cost of opening the position and also cost of reducing it.
        commission is expressed in currency units
    risk_as_percent: float
        max percentage risk that we aim to have on this instrument.
        for example it could be the the percentage that is used to calculate the stop price.
    """

    def __init__(self, start_time: datetime, end_time: datetime, contract: Contract, quantity: int, entry_price: float,
                 exit_price: float, commission: float, risk_as_percent: float = float('nan')):
        self.start_time = start_time
        self.end_time = end_time
        self.contract = contract
        self.quantity = quantity
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.commission = commission

        self.risk_as_percent = risk_as_percent

        self._multiplier = self.quantity * self.contract.contract_size

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
        profit_loss = (self.exit_price - self.entry_price) * self._multiplier - self.commission
        return profit_loss

    @property
    def total_risk(self) -> float:
        """
        total risk associated with a trade expressed in currency units.
        It is the maximum loss that we expect to get while holding 'self.quantity' units of 'self.contract'
        """
        total_risk = abs(self.entry_price * self.risk_as_percent * self._multiplier)
        return total_risk

    @property
    def r_multiply(self) -> float:
        """
        R multiply is the ratio of (profit or loss) to (total risk)
        """
        result = self.pnl / self.total_risk
        return result

    def __str__(self):
        string_template = "{class_name:s} ({start_date:s} - {end_date:s}) -> " \
                          "Asset: {asset:>20}, " \
                          "Quantity: {quantity:>8}, " \
                          "P&L: {pnl:>10.2f}".format(class_name=self.__class__.__name__,
                                                     start_date=date_to_str(self.start_time),
                                                     end_date=date_to_str(self.end_time),
                                                     asset=self.contract.symbol,
                                                     quantity=self.quantity,
                                                     pnl=self.pnl,
                                                     )

        return string_template
