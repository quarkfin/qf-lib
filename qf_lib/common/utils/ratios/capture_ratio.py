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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries


def capture_ratio(strategy: QFSeries, benchmark: QFSeries, upside_capture: bool,
                  frequency: Frequency = Frequency.MONTHLY) -> float:
    """
    Upside / Downside Capture Ratio
    This ratio is a statistical measure of a Fund Manager's overall performance in down or up markets.
    For example Downside Capture Ratio is used to evaluate how well or poorly the Manager performed
    relative to a specific index during periods when that index has dropped (had negative returns).
    The ratio is calculated by dividing the Strategy returns by the returns of the index during the down-market
    Downside Capture Ratio = sum(Strategy  Returns) / sum(Index Returns)

    A Fund Manager who has a downside capture ratio less than 1 has outperformed the index during the down-market
    by falling less than the index. For instance, a ratio of 0.75 indicates that the portfolio declined only 75%
    as much as the index during the period under consideration.

    Parameters
    ----------
    strategy:
        series of the strategy that will be evaluated
    benchmark:
        series of the benchmark for the strategy
    upside_capture: bool
        True - for upside capture ratio
        False - for downside capture ratio
    frequency: Frequency
        Frequency on which the the ratio is evaluated.
        For example Frequency.MONTHLY will result in evaluating the ration based on Monthly returns.

    Returns
    -------
    float
    """

    aggregated_strategy = get_aggregate_returns(strategy, frequency)
    aggregated_benchmark = get_aggregate_returns(benchmark, frequency)

    if upside_capture:
        selected_dates = aggregated_benchmark.loc[aggregated_benchmark > 0].index
    else:
        selected_dates = aggregated_benchmark.loc[aggregated_benchmark < 0].index

    selected_strategy_returns = aggregated_strategy.loc[selected_dates]
    selected_benchmark_returns = aggregated_benchmark.loc[selected_dates]
    benchmark_sum = selected_benchmark_returns.sum()

    if benchmark_sum != 0.0 and is_finite_number(benchmark_sum):
        return selected_strategy_returns.sum() / selected_benchmark_returns.sum()
    return float('nan')
