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
from typing import List, Tuple

from matplotlib.dates import MonthLocator, num2date, YearLocator
from matplotlib.ticker import FuncFormatter

from qf_lib.common.enums.orientation import Orientation
from qf_lib.common.utils.dateutils.get_quarter import get_quarter
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator
from qf_lib.plotting.decorators.axes_locator_decorator import AxesLocatorDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.series_line_decorator import SeriesLineDecorator
from qf_lib.plotting.decorators.span_decorator import SpanDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_bar_chart(
        series_list: List[QFSeries], names_list, title: str, lines: List[QFSeries], recession_series: QFSeries = None,
        start_x: datetime = None, end_x: datetime = None, quarterly: bool = False,
        date_label_format: Tuple[str, str] = ("%Y", "%y Q{}"), recession_name: str = None) -> BarChart:
    """
    Creates a new bar chart based on the settings specified.

    This function makes some assumptions about the type of bar chart to create, but it should cover >90% of cases.

    Parameters
    ----------
    series_list: List[QFSeries]
    names_list
    title: str
    lines: List[QFSeries]
        One or more series representing the lines to draw on the bar chart.
    recession_series: QFSeries
        A series that will be used to highlight recession periods using gray boxes.
    start_x: datetime
        The first date to plot from the specified series.
    end_x: datetime
        The last date to plot from the specified series.
    quarterly: bool
        Whether the bar chart should be formatted for quarterly frequency series.
    date_label_format: Tuple[str, str]
        The format for the date labels in the x-axis. It can contain a format parameter which will be replaced with
        the quarter. The first format is for labels that are not shown every quarter, whereas the second format is
        used for labels that are shown on every quarter.
    recession_name: str
        Example "US Recession"

    Returns
    -------
    BarChart
        A new bar chart.
    """
    assert len(names_list) > len(lines) + 1, \
        "Not all labels have been specified. Specify one in the list for each series and line."

    bar_chart = BarChart(orientation=Orientation.Vertical, start_x=start_x, end_x=end_x,
                         thickness=60 if quarterly else 20, align="center")
    bar_chart.tick_fontweight = "bold"
    bar_chart.tick_color = "black"

    series_start = series_list[0].index.min()
    series_end = series_list[0].index.max()
    data_elements = []
    for series in series_list:
        # Find the smallest series start and largest series end among all series.
        if series.index.min() < series_start:
            series_start = series.index.min()
        if series.index.max() > series_end:
            series_end = series.index.max()
        # Add the series to the bar chart.
        data_element = DataElementDecorator(series)
        data_elements.append(data_element)
        bar_chart.add_decorator(data_element)

    # Get the list of colors from the current stylesheet.
    style_colors = Chart.get_axes_colors()
    line_decorators = []
    for i in range(0, len(lines)):
        # Grab colors from the end so that they do not clash with the bars.
        color = style_colors[(len(style_colors) - i % len(style_colors)) - 1]
        # Add a series line decorator for each line.
        line_decorator = SeriesLineDecorator(
            lines[i][start_x:end_x], key="series_line_" + str(i), linewidth=4, color=color)
        line_decorators.append(line_decorator)

        bar_chart.add_decorator(line_decorator)

    # Create a title.
    if title is not None:
        title_decorator = TitleDecorator(title, key="title")
        bar_chart.add_decorator(title_decorator)

    # Create a legend.
    legend_decorator = _create_legend(bar_chart, data_elements, line_decorators, names_list, quarterly)

    # Create spans (rectangles) to highlight the recession periods.
    if recession_series is not None:
        span_decorator = SpanDecorator.from_int_list(recession_series, key="span")
        bar_chart.add_decorator(span_decorator)
        if recession_name is not None:
            legend_decorator.add_entry(span_decorator, recession_name)

    if quarterly:
        # Format the ticks.
        # Determine (roughly) how many years passed between ``start`` and ``end``.
        display_start = series_start if start_x is None else start_x
        display_end = series_end if end_x is None else end_x
        years = (display_end - display_start).days // 365
        # Determine how often to show the ticks.
        # N.B. The show_every value depends on the locator defined below.
        if years < 2:
            show_every = 1  # Every quarter.
            date_format = date_label_format[1]
        elif years > 10:
            show_every = 5  # Every 5 years.
            date_format = date_label_format[0]
        else:
            show_every = 4  # Every year (4 quarters).
            date_format = date_label_format[0]

        def func(x, pos):
            return _quarterly_formatter(x, pos, show_every, date_format)
        axes_formatter = AxesFormatterDecorator(x_major=FuncFormatter(func), key="formatter")
        bar_chart.add_decorator(axes_formatter)

        # Set the tick locator.
        if years > 10:
            x_major = YearLocator()
        else:
            x_major = MonthLocator(range(1, 13), bymonthday=30, interval=3)
        axes_locator = AxesLocatorDecorator(x_major=x_major, key="locator")
        bar_chart.add_decorator(axes_locator)

    return bar_chart


def _quarterly_formatter(x, pos: int, show_every: int, date_label_format):
    x = num2date(x)
    if pos is None:
        return x
    else:
        if pos % show_every == 0:
            return x.strftime(date_label_format.format(get_quarter(x)))
        else:
            return ""


def _create_legend(bar_chart, data_elements, line_decorators, names_list, quarterly: bool) -> LegendDecorator:
    legend_decorator = LegendDecorator(key='legend')

    i = 0
    for data_element in data_elements:
        bar_label = names_list[i]
        if bar_label is not None:
            date = data_element.data.index[-1]
            formatted_date = date.strftime("%b %y")
            if quarterly:
                formatted_date = "Q{} {}".format(str(date.quarter), date.year)
            last_date_label = " [{}]".format(formatted_date)
            legend_decorator.add_entry(data_element, bar_label + last_date_label)
        i += 1

    for line_decorator in line_decorators:
        series_label = names_list[i]
        if series_label is not None:
            legend_decorator.add_entry(line_decorator, series_label)
        i += 1

    bar_chart.add_decorator(legend_decorator)
    return legend_decorator
