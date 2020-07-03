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

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def kelly(qf_series: QFSeries) -> float:
    """
    Calculates the value of the Kelly Criterion (the fraction of money that should be invested) for the series
    of returns/prices.

    Kelly Criterion assumptions:
    1. You trade the same way you traded in the past.
    2. Each return corresponds to one trade.
    3. Returns are normally distributed (calculated value will be close to the ideal kelly value even for highly skewed
    returns. Test showed that the difference of up to 10% (relative) might occur for extremely skewed distributions.

    Parameters
    ----------
    qf_series: QFSeries
        timeseries of returns/prices. Each return/price must correspond to one trade.

    Returns
    -------
    float
        fraction of money that should be invested
    """

    # it is important to convert a series to simple returns and not log returns
    returns_tms = qf_series.to_simple_returns()  # type: SimpleReturnsSeries

    mean = returns_tms.mean()
    variance = returns_tms.var()

    kelly_criterion_value = mean / variance
    return kelly_criterion_value


def kelly_binary(win_probability: float, win_size: float, lose_size: float) -> float:
    """
    Calculates the value of the Kelly Criterion (the fraction of money that should be invested) for a bet
    that has two possible outcomes.

    NOTE: This method should not be used to estimate the kelly value for a timeseries.

    Parameters
    ----------
    win_probability:float
        probability of winning. Assumes that probability of losing is 1 - win_probability.
    win_size: float
        gain if we win.
        For example: 0.7 means that we get additional 70% of what we bet. (if we bet 10$ and we win we now have 17$)
        new_value = old_value * (1 + win_size)
    lose_size: float
        lose if we lose. This value should be negative.
        For example: -0.2 means that we lose 20% of what we bet. (if we bet 10$ and we lose we now have 8$)
        new_value = old_value * (1 + lose_size)
    Returns
    -------
    float
        fraction of money that should be invested

    """

    kelly_value = (-win_size * win_probability + lose_size * win_probability - lose_size) / (win_size * lose_size)
    return kelly_value
