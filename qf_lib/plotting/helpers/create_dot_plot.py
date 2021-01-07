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

import pandas as pd

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.point_emphasis_decorator import PointEmphasisDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_dot_plot(series1: QFSeries, series2: QFSeries, x_label: str, y_label: str,
                    start_x: float = None, end_x: float = None) -> LineChart:
    """Create a dot linechart.

    Parameters
    -----------
    series1: QFSeries
    series2: QFSeries
    x_label: str
    y_label: str
    start_x: float
    end_x: float

    Returns
    --------
    LineChart
    """

    # Combine the series.
    combined = pd.concat([series1, series2], axis=1)
    combined_series = QFSeries(data=combined.iloc[:, 0].values, index=combined.iloc[:, 1].values)

    # Create a new line chart.
    line_chart = LineChart(start_x=start_x, end_x=end_x)
    line_chart.tick_fontweight = "bold"
    line_chart.tick_color = "black"

    # Add the data.
    data_element = DataElementDecorator(combined_series, marker="o")
    line_chart.add_decorator(data_element)

    # Add a title.
    title_decorator = TitleDecorator("US Beveridge Curve", key="title")
    line_chart.add_decorator(title_decorator)

    # Add axes labels.
    axes_label_decorator = AxesLabelDecorator(x_label=x_label, y_label=y_label)
    line_chart.add_decorator(axes_label_decorator)

    # Emphasise the last point.
    # This series has many NaNs, we want to retrieve the last non-NaN point.
    no_nans = combined_series.dropna()
    point_to_emphasise = (no_nans.index[len(no_nans) - 1],
                          no_nans.values[len(no_nans) - 1])
    point_emphasis_decorator = PointEmphasisDecorator(
        data_element, point_to_emphasise, color="#CC1414", decimal_points=1, label_format="")
    line_chart.add_decorator(point_emphasis_decorator)

    # Create a legend.
    legend_decorator = LegendDecorator()
    last_date = series1.dropna().index.max()
    legend_decorator.add_entry(point_emphasis_decorator, "Latest ({:g}, {:g}) [{}]".format(
        point_to_emphasise[0], point_to_emphasise[1], last_date.strftime("%b %y")))
    line_chart.add_decorator(legend_decorator)

    return line_chart
