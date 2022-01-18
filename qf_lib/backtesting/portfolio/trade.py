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

from qf_lib.common.tickers.tickers import Ticker
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
    ticker: Ticker
        Ticker defining the security.
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

    def __init__(self, start_time: datetime, end_time: datetime, ticker: Ticker, pnl: float, commission: float,
                 direction: int, percentage_pnl: float = float('nan')):
        self.start_time = start_time
        self.end_time = end_time
        self.ticker = ticker

        self.pnl = pnl
        self.commission = commission
        self.direction = direction

        self.percentage_pnl = percentage_pnl

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Trade):
            return False

        return (self.ticker, self.start_time, self.end_time, self.pnl, self.commission, self.direction,
                self.percentage_pnl) == (other.ticker, other.start_time, other.end_time, other.pnl, other.commission,
                                         other.direction, other.percentage_pnl)

    def __str__(self):
        string_template = f"{self.__class__.__name__} ({date_to_str(self.start_time)} - " \
                          f"{date_to_str(self.end_time)}) -> " \
                          f"Asset: {self.ticker:>20}, " \
                          f"Direction: {self.direction:>8}, " \
                          f"P&L %: {self.percentage_pnl:>10.2%}, " \
                          f"P&L: {self.pnl:>10.2f}"

        return string_template
