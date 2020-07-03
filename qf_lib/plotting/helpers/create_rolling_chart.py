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

from typing import Union, List, Callable

import numpy
import pandas

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_rolling_chart(
        series: Union[QFSeries, List[QFSeries]], func: Callable[[Union[QFSeries, numpy.ndarray]], float],
        func_name: str, window_size: int = 126, step: int = 20, oos_date: str = None) -> LineChart:
    """
    Creates a new line chart and adds the rolling window for each of the specified series to it. The `func`
    function is fed data for each window and whatever it returns is added to the resulting rolled series.

    For example:

    .. code-block::python
        create_rolling_chart([strategy_tms, benchmark_tms],
                             lambda window: sharpe_ratio(PricesSeries(window), Frequency.DAILY),
                             "Sharpe Ratio", oos_date=oos_date)

    Parameters
    ----------
    series: QFSeries, List[QFSeries]
        One or more series to apply the rolling window transformation on add to the resulting chart.
    func: Callable[[Union[QFSeries, numpy.ndarray]], float]
        Called for each window. Takes one argument which is part of a series corresponding to a window. Returns a float.
    func_name: str
        Used in the title to specify the function that was called.
    window_size: int
    step: int
    oos_date: str
        only the OOS date of the first series in the list will be taken into account

    Returns
    -------
    LineChart
    """

    chart = LineChart()

    # Add a legend.
    legend = LegendDecorator()
    chart.add_decorator(legend)

    series_list = series
    if isinstance(series_list, QFSeries):
        series_list = [series_list]
    assert isinstance(series_list, list)

    for tms in series_list:
        rolling = tms.rolling_window(window_size, func, step=step)
        rolling_element = DataElementDecorator(rolling)
        chart.add_decorator(rolling_element)
        legend.add_entry(rolling_element, tms.name)

    # Add title
    chart.add_decorator(TitleDecorator(
        "Rolling {} (window: {}, step: {}) ".format(func_name, window_size, step)))

    # Add OOS line.
    new_oos_date = series_list[0].index.asof(pandas.to_datetime(oos_date))
    line = VerticalLineDecorator(new_oos_date, color='orange', linestyle="dashed")
    chart.add_decorator(line)

    return chart
