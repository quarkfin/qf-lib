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

from typing import Union, Tuple

import numpy as np
import scipy.stats as stats

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.ratios.sharpe_ratio import sharpe_ratio
from qf_lib.containers.series.qf_series import QFSeries


def minBTL(number_of_trials: Union[int, QFSeries], estimated_maximum: float = 1.0) -> Union[Tuple, QFSeries]:
    """
    MINBTL Calculates the minimum length of backtest given the number of trials during optimising
    the strategy. The function assumes that the distribution of qualities (e.g. Sharpe Ratios) is a normal
    distribution (mu=0, sig=1).

    The concept of the Minimum Backtest Length is presented by Bailey, Borwein, Prado and Zhu in  the
    'PseudoMathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance'.

    Parameters
    ----------
    number_of_trials: Union[int, QFSeries],
        the number of trials made during optimising the algorithm (can be a QFSeries of ints)
    estimated_maximum: float
        estimated maximum value of a quality (e.g. Sharpe Ratio) (by default: 1)

    Returns
    --------
    Union[float, QFSeries]
        float defining minimum backtest length in case if the number_of_trials was an integer
        QFSeries with the minBTL values, where the index is given by the number_of_trials QFSeries
    """

    samples_numbers = [number_of_trials] if isinstance(number_of_trials, int) else sorted(number_of_trials.values)
    minBTL_values = []

    for samples_number in samples_numbers:
        expected_maximum = (1 - np.euler_gamma) * stats.norm.ppf(1 - 1 / samples_number, loc=0, scale=1) + \
                           np.euler_gamma * stats.norm.ppf(1 - 1 / samples_number * np.exp(-1))

        minimum_backtest_length = (expected_maximum / estimated_maximum) ** 2
        minBTL_values.append(minimum_backtest_length)

    result = QFSeries(data=minBTL_values, index=samples_numbers)
    if len(samples_numbers) == 1:
        result = result.iloc[0]
    return result


def minTRL(returns_timeseries: QFSeries, target_sharpe_ratio: float = 1.0, confidence_level: float = 0.95) -> float:
    """
    Computes the Minimum Track Record Length measure. The aim of computing is the possibility of answering the
    following question: 'How long should a track record be in order to have statistical confidence that its Sharpe ratio
    is above a given threshold?'

    The concept of Minimum Track Record Length is presented by Bailey and Prado in 'The Sharpe Ratio Efficient Frontier'
    """
    returns_series = returns_timeseries.to_simple_returns()
    skewness = returns_series.skew()
    kurtosis = returns_series.kurt()
    sharpe_ratio_value = sharpe_ratio(returns_series, frequency=Frequency.DAILY)

    minTRL_value = 1 + ((1 - skewness * sharpe_ratio_value + (kurtosis - 1) / 4.0) * sharpe_ratio_value ** 2) * \
        (stats.norm.ppf(confidence_level) / (sharpe_ratio_value - target_sharpe_ratio)) ** 2
    return minTRL_value
