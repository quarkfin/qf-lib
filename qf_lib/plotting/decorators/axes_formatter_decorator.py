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

from typing import Any

import matplotlib
from matplotlib.ticker import Formatter

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesFormatterDecorator(ChartDecorator):
    """
    Creates a new Axes Formatter decorator that changes the way tickers in the x/y-axis are displayed.

    See here for a list of valid axes formatters: http://matplotlib.org/api/ticker_api.html#tick-formatting.

    Parameters
    -----------
    x_major: Formatter
    x_minor: Formatter
    y_major: Formatter
    y_minor: Formatter
    use_secondary_axes: bool
        use secondary axes (by default False)
    key: str
        see: ChartDecorator.__init__#key
    """
    def __init__(self, x_major: Formatter = None, x_minor: Formatter = None, y_major: Formatter = None,
                 y_minor: Formatter = None, use_secondary_axes: bool = False, key: str = None):
        super().__init__(key)
        self._x_major = x_major
        self._x_minor = x_minor
        self._y_major = y_major
        self._y_minor = y_minor
        self._use_secondary_axes = use_secondary_axes

    def decorate(self, chart: "Chart"):
        if self._use_secondary_axes:
            ax = chart.secondary_axes
        else:
            ax = chart.axes

        if self._x_major is not None:
            ax.xaxis.set_major_formatter(self._x_major)
        if self._x_minor is not None:
            ax.xaxis.set_minor_formatter(self._x_minor)
        if self._y_major is not None:
            ax.yaxis.set_major_formatter(self._y_major)
        if self._y_minor is not None:
            ax.yaxis.set_minor_formatter(self._y_minor)


class PercentageFormatter(Formatter):
    """
    Formats data as percentages on charts (e.g. 0.1 => 10%).
    """

    def __init__(self, value_format: str = ".0f"):
        self.value_format = value_format

    def __call__(self, x: Any, pos=None):
        format_str = ('{:' + self.value_format + '}' + self.percent_sign())
        return format_str.format(100 * x)

    @classmethod
    def percent_sign(cls) -> str:
        if matplotlib.rcParams['text.usetex'] is True:
            percent_sign = r'$\%$'  # The percent symbol needs escaping in latex
        else:
            percent_sign = '%'

        return percent_sign
