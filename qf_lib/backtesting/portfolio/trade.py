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


class Trade:
    """
    Trade is a logical unit representing getting exposure to the market (long or short) finished by closing the
    position. Trade begins with new position opened and finishes when the position is closed.
    Note: For futures contracts, automated rolling of the contract will result in closing the existing exposure on the
    specific ticker, and therefore will generate a trade.

    Parameters
    -----------
    start_time: datetime
        Moment when we opened the position corresponding to this trade.
    end_time: datetime
        Moment when we close the trade.
    contract: Contract
        Contract defining the security.
    pnl: float
        Profit or loss associated with a trade expressed in currency units including transaction costs and commissions.
    commission: float
        All the transaction costs related to the trade. It includes the cost of opening the position and also cost
        of reducing it. Expressed in currency units.
    direction: int
        Direction of the position: Long = 1, Short = -1. Defined by the initial transaction.
    percentage_pnl: float
       Total pnl divided by the most recent value of the portfolio.
    """

    def __init__(self, start_time: datetime, end_time: datetime, contract: Contract, pnl: float, commission: float,
                 direction: int, percentage_pnl: float = float('nan')):
        self.start_time = start_time
        self.end_time = end_time
        self.contract = contract

        self.pnl = pnl
        self.commission = commission
        self.direction = direction

        self.percentage_pnl = percentage_pnl

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Trade):
            return False

        return (self.contract, self.start_time, self.end_time, self.pnl, self.commission, self.direction,
                self.percentage_pnl) == (other.contract, other.start_time, other.end_time, other.pnl, other.commission,
                                         other.direction, other.percentage_pnl)

    def __str__(self):
        string_template = "{class_name:s} ({start_date:s} - {end_date:s}) -> " \
                          "Asset: {asset:>20}, " \
                          "Direction: {direction:>8}, " \
                          "P&L %: {percentage_pnl:>10.2%}, " \
                          "P&L: {pnl:>10.2f}".format(class_name=self.__class__.__name__,
                                                     start_date=date_to_str(self.start_time),
                                                     end_date=date_to_str(self.end_time),
                                                     direction=self.direction,
                                                     asset=self.contract.symbol,
                                                     percentage_pnl=self.percentage_pnl,
                                                     pnl=self.pnl,
                                                     )

        return string_template
