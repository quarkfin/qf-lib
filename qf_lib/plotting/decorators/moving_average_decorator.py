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


class MovingAverageDecorator(ChartDecorator, SimpleLegendItem):
    """
    Creates a new decorator which draws a moving average line.

    Parameters
    ----------
    window_size: int
       window size which will be used to draw moving average line
    series: QFSeries
       series to calculate the moving average line for
    plot_settings: Any
       additional plot settings for matplotlib
    """

    def __init__(self, window_size: int, series: QFSeries, key: str = None, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self.window_size = window_size
        self.series = series
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart"):
        rolling_series = self.series.rolling_window(self.window_size, lambda x: x.mean(), optimised=True)
        series_handle = chart.axes.plot(rolling_series, **self.plot_settings)[0]
        self.legend_artist = series_handle
