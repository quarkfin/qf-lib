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

from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.series.prices_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.axes_formatter_decorator import PercentageFormatter
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class UnderwaterDecorator(ChartDecorator):
    """
    Underwater chart decorator

    Parameters
    ----------
    series: QFSeries
        prices series for which the underwater plot is constructed
    colors_alpha: float
        sets the level of transparency of the cone
    key: str
        see ChartDecorator.key.__init__#key
    """
    def __init__(self, series: QFSeries, colors_alpha: float = 1.0, key: str = None):
        super().__init__(key)
        self.series = series
        self._colors_alpha = colors_alpha

    def decorate(self, chart: "Chart") -> None:
        drawdown_series = drawdown_tms(self.series)
        drawdown_series *= -1
        ax = chart.axes
        ax.yaxis.set_major_formatter(PercentageFormatter())
        ax.fill_between(drawdown_series.index, 0, drawdown_series.values, alpha=self._colors_alpha)
        ax.set_ylim(top=0)
