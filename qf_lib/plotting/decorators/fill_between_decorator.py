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

from typing import Union

from qf_lib.containers.series.prices_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class FillBetweenDecorator(ChartDecorator, SimpleLegendItem):
    """
    Fills the area between two lines

    Parameters
    ----------
    upper_bound: QFSeries
        upper bound of the filled area
    lower_bound: datetime
        lower bound of the filled area
    colors_alpha: float
        sets the level of transparency of the cone
    key: str
        see ChartDecorator.key.__init__#key
    plot_settings
        kwargs passed to the fill_between function
    """
    def __init__(self, upper_bound: QFSeries, lower_bound: Union[QFSeries, float] = 0.0, colors_alpha: float = 0.25,
                 key: str = None, **plot_settings):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self._upper_bound = upper_bound
        self._lower_bound = lower_bound
        self._colors_alpha = colors_alpha
        self._plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        ax = chart.axes
        handle = ax.fill_between(self._upper_bound.index, self._upper_bound, self._lower_bound,
                                 alpha=self._colors_alpha, **self._plot_settings)
        self.legend_artist = handle
