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

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class SeriesLineDecorator(ChartDecorator, SimpleLegendItem):
    """
    A simple decorator that displays a single series, useful for charts that want a line overlay for example bar chart.
    """

    def __init__(self, series: QFSeries, key: str = None, use_secondary_axes: bool = False, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self._series = series
        self.use_secondary_axes = use_secondary_axes
        self.plot_settings = plot_settings

    def decorate(self, chart):
        axes = chart.axes
        if self.use_secondary_axes:
            chart.setup_secondary_axes_if_necessary()
            axes = chart.secondary_axes

        self.legend_artist = axes.plot(self._series, **self.plot_settings)[0]
