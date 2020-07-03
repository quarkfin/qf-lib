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
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.point_emphasis_decorator import PointEmphasisDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_skewness_chart(series: QFSeries, title: str = None) -> LineChart:
    """
    Creates a new line chart showing the skewness of the distribution.
    It plots original series together with another series which contains sorted absolute value of the returns

    Parameters
    ----------
    series: QFSeries
        ``QFSeries`` to plot on the chart.
    title: str
        title of the graph, specify ``None`` if you don't want the chart to show a title.

    Returns
    -------
    LineChart
        The constructed ``LineChart``.
    """

    original_price_series = series.to_prices(1)

    # Construct a series with returns sorted by their amplitude
    returns_series = series.to_simple_returns()
    abs_returns_series = returns_series.abs()

    returns_df = pd.concat([returns_series, abs_returns_series], axis=1, keys=['simple', 'abs'])
    sorted_returns_df = returns_df.sort_values(by='abs')
    skewness_series = SimpleReturnsSeries(index=returns_series.index, data=sorted_returns_df['simple'].values)
    skewed_price_series = skewness_series.to_prices(1)

    # Create a new Line Chart.
    line_chart = LineChart(start_x=series.index[0], rotate_x_axis=True)

    # Add original series to the chart
    original_series_element = DataElementDecorator(original_price_series)
    line_chart.add_decorator(original_series_element)

    skewed_series_element = DataElementDecorator(skewed_price_series)
    line_chart.add_decorator(skewed_series_element)

    # Add a point at the end
    point = (skewed_price_series.index[-1], skewed_price_series[-1])
    point_emphasis = PointEmphasisDecorator(skewed_series_element, point, font_size=9)
    line_chart.add_decorator(point_emphasis)

    # Create a title.
    if title is not None:
        title_decorator = TitleDecorator(title, "title")
        line_chart.add_decorator(title_decorator)

    # Add a legend.
    legend_decorator = LegendDecorator(key='legend')
    legend_decorator.add_entry(original_series_element, 'Chronological returns')
    legend_decorator.add_entry(skewed_series_element, 'Returns sorted by magnitude')
    line_chart.add_decorator(legend_decorator)
    line_chart.add_decorator(AxesLabelDecorator(y_label="Profit/Loss"))

    return line_chart
