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

from collections import Sequence
from typing import Any

from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class ScatterDecorator(ChartDecorator, SimpleLegendItem):
    """
    Creates a scatter plot based on the data specified.

    Parameters
    ----------
    x_data: Sequence
       values of x coordinate
    y_data: Sequence
       values of y coordinate
    size: int
       size in points^2; scalar or an array of the same length as x_data and y_data
    color
       *c* can be a single color format string, or a sequence of color specifications of length x_data and y_data,
       or a sequence of x_data and y_data numbers to be mapped to colors using the *cmap* and *norm* specified via
       kwargs (see below). Note that color should not be a single numeric RGB or RGBA sequence because that is
       indistinguishable from an array of values to be colormapped.  color can be a 2-D array in which the rows are
       RGB or RGBA, however, including the case of a single row to specify the same color for all points.
    plot_settings
       other settings like for example: alpha, linewidths, verts, edgecolors

    """

    def __init__(
            self, x_data: Sequence, y_data: Sequence, size: int = 40, color=None, key: str = None, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self.x_data = x_data
        self.y_data = y_data
        self.size = size
        if color is None:
            self.color = Chart.get_axes_colors()[0]
        else:
            self.color = color
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart"):
        self.legend_artist = chart.axes.scatter(
            self.x_data, self.y_data, s=self.size, c=self.color, **self.plot_settings)
