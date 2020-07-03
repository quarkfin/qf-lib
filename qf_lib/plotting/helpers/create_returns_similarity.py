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

from sklearn import preprocessing

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.kde_chart import KDEChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_returns_similarity(strategy: QFSeries, benchmark: QFSeries, mean_normalization: bool = True,
                              std_normalization: bool = True, frequency: Frequency = None) -> KDEChart:
    """
    Creates a new returns similarity chart. The frequency is determined by the specified returns series.

    Parameters
    ----------
    strategy: QFSeries
        The strategy series to plot.
    benchmark: QFSeries
        The benchmark series to plot.
    mean_normalization: bool
        Whether to perform mean normalization on the series data.
    std_normalization: bool
        Whether to perform variance normalization on the series data.
    frequency: Frequency
        Returns can be aggregated in to specific frequency before plotting the chart
    Returns
    -------
    KDEChart
        A newly created KDEChart instance.
    """
    chart = KDEChart()
    colors = Chart.get_axes_colors()

    if frequency is not None:
        aggregate_strategy = get_aggregate_returns(strategy.to_simple_returns(), frequency)
        aggregate_benchmark = get_aggregate_returns(benchmark.to_simple_returns(), frequency)
    else:
        aggregate_strategy = strategy.to_simple_returns()
        aggregate_benchmark = benchmark.to_simple_returns()

    scaled_strategy = preprocessing.scale(
        aggregate_strategy, with_mean=mean_normalization, with_std=std_normalization)
    strategy_data_element = DataElementDecorator(
        scaled_strategy, bw="scott", shade=True, label=strategy.name, color=colors[0])
    chart.add_decorator(strategy_data_element)

    scaled_benchmark = preprocessing.scale(
        aggregate_benchmark, with_mean=mean_normalization, with_std=std_normalization)
    benchmark_data_element = DataElementDecorator(
        scaled_benchmark, bw="scott", shade=True, label=benchmark.name, color=colors[1])
    chart.add_decorator(benchmark_data_element)

    # Add a title.
    title = _get_title(mean_normalization, std_normalization, frequency)
    title_decorator = TitleDecorator(title, key="title")
    chart.add_decorator(title_decorator)
    chart.add_decorator(AxesLabelDecorator("Returns", "Similarity"))
    return chart


def _get_title(with_mean, with_std, frequency):
    if with_mean:
        if with_std:
            title = "Ret. Sim. w. mean & var norm."
        else:
            title = "Ret. Sim. w. mean normalization"
    else:
        if with_std:
            title = "Ret. Sim. w. var. normalization"
        else:
            title = "Returns Similarity"

    if frequency is not None:
        freq = str(frequency).capitalize()
        return freq + " " + title
    else:
        return title
