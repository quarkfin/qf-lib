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

from itertools import cycle
from typing import List

from qf_lib.common.utils.returns.list_longest_drawdowns import list_longest_drawdowns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class TopDrawdownDecorator(ChartDecorator):
    """
    Highlights the top drawdowns in a specified series.

    The top ``count`` amount of drawdowns will be highlighted. If ``colors`` is ``None`` then a default list of
    colours will be used, you can override it by specifying a list of strings containing color names or hex codes.

    Parameters
    ----------
    prices: QFSeries
        A series from which drawdowns will be calculated.
    count: int
        The amount of longest drawdowns to highlight.
    colors: List[str]
        A list of colours to use to highlight the drawdowns.
    """

    def __init__(self, prices: QFSeries, count: int, colors: List[str] = None, key: str = None):
        super().__init__(key)
        if colors is None:
            self._color = Chart.get_axes_colors()[3]
        else:
            self._color = cycle(colors)
        self._current_color = 0

        self._series = prices
        self._count = count

    def decorate(self, chart: "Chart"):

        for drawdown in list_longest_drawdowns(self._series, self._count):
            chart.axes.axvspan(drawdown[0], drawdown[1], alpha=0.2, color=self._color)
