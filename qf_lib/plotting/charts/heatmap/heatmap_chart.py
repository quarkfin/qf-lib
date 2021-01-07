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

from typing import Any, Tuple

import matplotlib as mpl

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.plotting.charts.chart import Chart


class HeatMapChart(Chart):
    """
    Creates a Heatmap chart.

    Parameters
    ----------
    data: QFDataFrame
        QFDataFrame containing data that should be plotted using heat map
    color_map
        color map to use for coloring the heat map
    min_value: float
        min possible value (used for adjusting colors on the heatmap)
    max_value: float
        max possible value (used for adjusting colors on the heatmap)
    start_x: Any
        see: Chart__init__#start_x
    end_x: Any
        see: Chart__init__#end_x
    """
    def __init__(self, data: QFDataFrame, color_map=None, min_value: float = None, max_value: float = None,
                 start_x: Any = None, end_x: Any = None):
        super().__init__(start_x, end_x)
        self.data = data[::-1]  # for proper plotting the matrix needs to be reversed
        self.color_map = color_map if color_map is not None else mpl.cm.Blues
        self.min_value = min_value
        self.max_value = max_value

        self.color_mesh_ = None
        """ Mesh generated during plotting. """

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)
        self._draw_heatmap()
        self._set_ticks()
        self._adjust_style()
        self._apply_decorators()

    def _draw_heatmap(self):
        self.color_mesh_ = self.axes.pcolormesh(
            self.data, cmap=self.color_map, vmin=self.min_value, vmax=self.max_value)
        self.color_mesh_.update_scalarmappable()  # update info about colors in the mesh

    def _set_ticks(self):
        columns_number = self.data.shape[1]
        rows_number = self.data.shape[0]
        self.axes.xaxis.set_ticks([i + 0.5 for i in range(columns_number)])
        self.axes.yaxis.set_ticks([i + 0.5 for i in range(rows_number)])
