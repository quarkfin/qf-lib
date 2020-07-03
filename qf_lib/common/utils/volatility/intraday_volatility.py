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

from numpy import std, sqrt

from qf_lib.containers.series.returns_series import ReturnsSeries


def intraday_volatility(returns: ReturnsSeries, interval_in_minutes: int) -> float:
    """
    Calculates annualised volatility from intraday samples of given interval.

    Parameters
    ----------
    returns: ReturnsSeries
        timeseries of intraday returns
    interval_in_minutes: int
        interval between samples (in minutes)

    Returns
    -------
    float
        annualized intraday volatility calculated from intraday returns
    """
    unannualized_volatility = std(returns.values)

    minutes_in_trading_day = 390  # 6.5h * 60 min/h = 390min
    intervals_in_day = minutes_in_trading_day / interval_in_minutes
    business_days_per_year = 252

    return unannualized_volatility * sqrt(intervals_in_day * business_days_per_year)
