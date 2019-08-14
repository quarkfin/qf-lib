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

from datetime import datetime, timedelta

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def sqn(trades: QFDataFrame):
    """
    Calculates the SQN = mean return of trade / std(returns of trades)
    """

    returns = trades[TradeField.Return]
    result = returns.mean() / returns.std()
    return result


def sqn_for100trades(trades: QFDataFrame):
    """
    Calculates the SQN = mean return of trade / std(returns of trades) * sqrt(100)
    """
    return sqn(trades) * 10


def avg_nr_of_trades_per1y(trades: QFDataFrame, start_date: datetime, end_date: datetime):
    """
    Calculates average number of trades per year for a given data-frame of trades.
    """
    returns = trades[TradeField.Return]
    period_length = end_date - start_date
    period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG
    avg_number_of_trades_1y = returns.count() / period_length_in_years
    return avg_number_of_trades_1y


def trade_based_cagr(trades: QFDataFrame, start_date: datetime, end_date: datetime):
    """
    Calculates average number of trades per year for a given data-frame of trades.
    """
    returns = trades[TradeField.Return]
    dates = trades[TradeField.EndDate]

    # insert start date and the beginning and end date at the end.
    # we insert nex start + 1day to returns and set the frequency for to_prices to daily so that the
    # prices series will start exactly from the start_date
    returns = pd.concat([pd.Series([0]), returns, pd.Series([0])])
    dates = pd.concat([pd.Series([start_date]), dates + timedelta(days=1), pd.Series([end_date])])

    returns_tms = SimpleReturnsSeries(index=dates, data=returns.values)
    prices_tms = returns_tms.to_prices(frequency=Frequency.DAILY)
    return cagr(prices_tms)


def trade_based_max_drawdown(trades: QFDataFrame):
    """
    Calculates the max drawdown on the series of returns of trades
    """
    if trades.shape[0] > 0:
        returns = trades[TradeField.Return]
        dates = trades[TradeField.EndDate]
        returns_tms = SimpleReturnsSeries(index=dates, data=returns.values)
        prices_tms = returns_tms.to_prices(frequency=Frequency.DAILY)
        return -max_drawdown(prices_tms)

    return None
