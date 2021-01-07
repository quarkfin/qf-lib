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
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.containers.series.qf_series import QFSeries


def sqn(returns: QFSeries):
    """
    Calculates the SQN = mean return of trade / std(returns of trades). The returns passed to the function may wither
    be defined as percentage PnL of trades or as r_multiply = percentage PnL / risk.
    """
    result = returns.mean() / returns.std()
    return result


def sqn_for100trades(returns: QFSeries):
    """
    Calculates the SQN = mean return of trade / std(returns of trades) * sqrt(100)
    """
    return sqn(returns) * 10


def avg_nr_of_trades_per1y(trades_returns: QFSeries, start_date: datetime, end_date: datetime):
    """
    Calculates average number of trades per year for a given data-frame of trades.
    """
    period_length = end_date - start_date
    period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG
    avg_number_of_trades_1y = len(trades_returns) / period_length_in_years
    return avg_number_of_trades_1y
