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

from scipy.stats import norm

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.line_decorators import DiagonalLineDecorator, VerticalLineDecorator, \
    HorizontalLineDecorator
from qf_lib.plotting.decorators.scatter_decorator import ScatterDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_qq_chart(strategy: QFSeries) -> Chart:
    """

    Parameters
    ----------
    strategy: QFSeries

    Returns
    -------
    Chart
    """
    colors = Chart.get_axes_colors()

    strategy = strategy.to_log_returns()
    # Normalize
    strategy = strategy - strategy.mean()
    strategy = strategy / strategy.std()
    # Sort
    strategy_values = sorted(strategy.values)

    # Create benchmark
    benchmark_values = list(range(1, len(strategy_values) + 1))
    n = len(strategy_values) + 1
    benchmark_values = map(lambda x: x / n, benchmark_values)
    benchmark_values = list(map(lambda x: norm.ppf(x), benchmark_values))

    # Figure out the limits.
    maximum = max(max(benchmark_values), max(strategy_values))

    result = LineChart(start_x=-maximum, end_x=maximum, upper_y=maximum, lower_y=-maximum)
    result.add_decorator(ScatterDecorator(
        benchmark_values, strategy_values, color=colors[0], alpha=0.6, edgecolors='black', linewidths=0.5))

    result.add_decorator(VerticalLineDecorator(0, color='black', linewidth=1))
    result.add_decorator(HorizontalLineDecorator(0, color='black', linewidth=1))

    result.add_decorator(TitleDecorator("Normal Distribution Q-Q"))
    result.add_decorator(AxesLabelDecorator("Normal Distribution Quantile", "Observed Quantile"))

    # Add diagonal line.
    result.add_decorator(DiagonalLineDecorator(color=colors[1]))

    return result
