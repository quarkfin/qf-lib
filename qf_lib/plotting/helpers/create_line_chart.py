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

from datetime import datetime
from typing import List, Union, Any

import pandas

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator, VerticalLineDecorator
from qf_lib.plotting.decorators.point_emphasis_decorator import PointEmphasisDecorator
from qf_lib.plotting.decorators.span_decorator import SpanDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_line_chart(
        data_list: List[Union[QFSeries, DataElementDecorator]], names_list, title: str = None,
        recession_series: QFSeries = None, horizontal_lines_list: List[float] = None,
        vertical_lines_list: List[float] = None, disable_dot: bool = False, start_x: datetime = None,
        end_x: datetime = None, upper_y: float = None, lower_y: float = None, dot_decimal_points: int = 2,
        recession_name: str = None) -> LineChart:
    """
    Creates a new line chart based on the settings specified.

    This function makes certain assumptions about the line chart, it can be customised via the parameters which should
    cover >90% of use cases. For more customisation use the ``LineChart`` class directly.

    Parameters
    ----------
    data_list: List[Union[QFSeries, DataElementDecorator]]
        A list of ``QFSeries`` or ``DataElementDecorator``s to plot on the chart.
    names_list: List[str]
        A list of strings specifying the labels for the series, horizontal and vertical lines respectively. ``None``
        can be specified for labels to not display it for a specific series, or line.
    title: str
        The title of the graph, specify ``None`` if you don't want the chart to show a title.
    recession_series: QFSeries
        A ``QFSeries`` specifying where recessions occurred on the chart, will be highlighted using grey rectangles
        on the graph.
    horizontal_lines_list: List[float]
        An optional list of values where a horizontal line should be drawn.
    vertical_lines_list: List[float]
        An optional list of values where a vertical line should be drawn.
    disable_dot: bool
        Whether a marker on the last point should be disabled.
    start_x: datetime
        The date where plotting should begin.
    end_x: datetime
        The date where plotting should end.
    upper_y: float
        The upper bound y-axis value at which plotting should begin.
    lower_y: float
        The lower bound y-axis value at which plotting should begin.
    dot_decimal_points: int
        How many decimal places to show after the decimal points when drawing text for "dot".
    recession_name: str
        A string specifying the recession label. If "None" or missing, will not be included.

    Returns
    -------
    LineChart
        The constructed ``LineChart``.
    """

    # If `end_x` was not specified, use a heuristic to determine it.
    if end_x is None and start_x is not None:
        end_x = LineChart.determine_end_x(start_x, data_list)

    # Create a new Line Chart.
    line_chart = LineChart(start_x=start_x, end_x=end_x, upper_y=upper_y, lower_y=lower_y)
    line_chart.tick_fontweight = "bold"
    line_chart.tick_color = "black"

    names_index = 0  # Current legend label.
    legend_decorator = LegendDecorator(key='legend')

    # Retrieve necessary data.
    for data in data_list:
        assert isinstance(data, (pandas.Series, DataElementDecorator))
        # Add the current series with a label taken from ``names_list``.
        data_element = data
        if isinstance(data_element, pandas.Series):
            data_element = DataElementDecorator(data)
        line_id = data_element.key
        line_chart.add_decorator(data_element)

        # Retrieve the last data point.
        point_to_emphasise = \
            (_get_last_valid_value(data_element.data.index), _get_last_valid_value(data_element.data.values))

        series_label = _get_name(names_list, names_index)
        if series_label is not None:
            legend_decorator.add_entry(
                data_element, series_label + " [{}]".format(point_to_emphasise[0].strftime("%b %y")))

        names_index += 1
        if not disable_dot:
            # Emphasise the last data point.
            point_emphasis = PointEmphasisDecorator(
                data_element, point_to_emphasise, decimal_points=dot_decimal_points,
                key="point_emphasis_{}".format(line_id), use_secondary_axes=data_element.use_secondary_axes)
            line_chart.add_decorator(point_emphasis)

    # Create a title.
    if title is not None:
        title_decorator = TitleDecorator(title, "title")
        line_chart.add_decorator(title_decorator)

    # Create spans (rectangles) to highlight the recession periods.
    if recession_series is not None:
        span_decorator = SpanDecorator.from_int_list(recession_series, "span")
        line_chart.add_decorator(span_decorator)
        if recession_name is not None:
            legend_decorator.add_entry(span_decorator, recession_name)

    # Create horizontal lines.
    if horizontal_lines_list is not None:
        for hline in horizontal_lines_list:
            line_decorator = HorizontalLineDecorator(hline, key="hline" + str(hline))
            line_chart.add_decorator(line_decorator)
            series_label = _get_name(names_list, names_index)
            if series_label is not None:
                legend_decorator.add_entry(line_decorator, series_label)

            names_index += 1

    # Create vertical lines.
    if vertical_lines_list is not None:
        for vline in vertical_lines_list:
            line_decorator = VerticalLineDecorator(vline, key="vline" + str(vline))
            line_chart.add_decorator(line_decorator)
            series_label = _get_name(names_list, names_index)
            if series_label is not None:
                legend_decorator.add_entry(line_decorator, series_label)
            names_index += 1

    # Add a legend.
    line_chart.add_decorator(legend_decorator)

    return line_chart


def _get_last_valid_value(list: List[Any]) -> Any:
    i = len(list) - 1
    while i >= 0:
        if not pandas.isnull(list[i]):
            return list[i]
        i -= 1

    raise Exception("Could not find non-NaN value inside list. Your series may be full of NaNs.")


def _get_name(names, index: int) -> str:
    if index > len(names) - 1:
        raise IndexError("Could not find Legend name at index {}. Pass `None` if you do not wish to "
                         "specify it.".format(index))
    return names[index]
