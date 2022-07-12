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
import math
import numpy as np

from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.orientation import Orientation
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.bar_values_decorator import BarValuesDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_returns_bar_chart(returns: QFSeries, frequency: Frequency = Frequency.YEARLY, title: str = None) -> BarChart:
    """
    Constructs a new returns bar chart based on the returns specified. By default, a new annual returns bar chart will
    be created.

    Parameters
    ----------
    returns: QFSeries
        The returns series to use in the chart.
    frequency: Frequency
        Frequency of the returns after aggregation
        It accepts YEARLY, MONTHLY, WEEKLY and DAILY frequencies
    title:
        optional title for the chart

    Returns
    --------
    BarChart
    """
    colors = Chart.get_axes_colors()
    # Calculate data.
    aggregate_returns = get_aggregate_returns(returns, frequency, multi_index=False)
    data_series = QFSeries(_convert_date(aggregate_returns, frequency).sort_index(ascending=True))

    chart = BarChart(Orientation.Horizontal, align="center")
    chart.add_decorator(DataElementDecorator(data_series, key="data_element"))
    chart.add_decorator(BarValuesDecorator(data_series))

    # Format the x-axis so that its labels are shown as a percentage.
    chart.add_decorator(AxesFormatterDecorator(x_major=PercentageFormatter()))

    # Format Y axis to make sure we have a tick for each year or 2 years
    data_series_length = len(data_series)
    if data_series_length > 10:
        data_series = data_series[np.arange(data_series_length) % math.ceil(data_series_length / 10) == 0]

    y_labels = data_series.index
    chart.add_decorator(AxisTickLabelsDecorator(labels=y_labels, axis=Axis.Y, tick_values=y_labels))

    # Add an average line.
    avg_line = VerticalLineDecorator(
        aggregate_returns.values.mean(), color=colors[1], key="avg_line", linestyle="--", alpha=0.8)
    chart.add_decorator(avg_line)

    # Add a legend.
    legend = LegendDecorator(key="legend_decorator")
    legend.add_entry(avg_line, "Mean")
    chart.add_decorator(legend)

    # Add a title.
    if title is None:
        title = str(frequency).capitalize() + " Returns"
    title = TitleDecorator(title, key="title_decorator")
    chart.add_decorator(title)
    chart.add_decorator(AxesLabelDecorator("Returns", "Year"))
    return chart


def _convert_date(data_series, frequency: Frequency):
    format_frequency = {
        Frequency.YEARLY: "%Y",
        Frequency.MONTHLY: "%Y %m",
        Frequency.WEEKLY: "%Y %V",
        Frequency.DAILY: "%Y %m %d"
    }

    return data_series.rename(index=lambda x: x.strftime(format_frequency[frequency]))
