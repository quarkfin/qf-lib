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
import warnings
from typing import Optional

import matplotlib as mpl
from matplotlib.ticker import Formatter
import numpy as np

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.common.enums.orientation import Orientation


class BarValuesDecorator(ChartDecorator):
    """
    Decorator for adding value annotations to a bar chart.

    This decorator takes a QFSeries object and annotates each bar in a bar chart with its corresponding value.
    Currently only non stacked BarCharts are supported

    Parameters
    ----------
    formatter: Optional[Formatter]
        formatter to additionally format the values
    key: str
        see ChartDecorator.key.__init__#key

    """

    def __init__(self, formatter: Optional[Formatter] = None, key: str = None):
        super().__init__(key)
        self._formatter = formatter

    def decorate(self, chart: "BarChart") -> None:
        if chart.stacked:
            raise NotImplementedError("Only non stacked BarCharts are supported at the moment.")

        font_size = mpl.rcParams['legend.fontsize']
        space = max(np.diff(chart.axes.get_xticks())) * 0.05 if chart.orientation == Orientation.Horizontal else max(np.diff(
            chart.axes.get_yticks())) * 0.05

        for container in chart.axes.containers:
            for bar in container:
                if chart.orientation == Orientation.Vertical:
                    value = bar.get_height()
                    x = bar.get_x() + bar.get_width() / 2
                    y = value + space if value > 0 else space
                elif chart.orientation == Orientation.Horizontal:
                    value = bar.get_width()
                    y = bar.get_y() + bar.get_height() / 2
                    x = value + space if value > 0 else space
                else:
                    continue

                if self._formatter is not None:
                    try:
                        formatted_value = self._formatter(value)
                    except TypeError as e:
                        formatted_value = value
                        warnings.warn(f"Could not format the value correctly with the given formatter due to {e}.")

                else:
                    formatted_value = f'{value:.2f}'

                chart.axes.text(x, y, formatted_value,
                                ha='center' if chart.orientation == Orientation.Vertical else 'left',
                                va='bottom' if chart.orientation == Orientation.Vertical else 'center',
                                size=font_size)

        # move the right limit of the x axis because some labels might go beyond the chart
        _, x_max = chart.axes.get_xlim()
