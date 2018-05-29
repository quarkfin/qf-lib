from typing import Any

import matplotlib as mpl
import pandas as pd

from qf_lib.plotting.charts.chart import Chart


class HeatMapChart(Chart):
    def __init__(self, data: pd.DataFrame, color_map=None, min_value: float=None, max_value: float=None,
                 start_x: Any=None, end_x: Any=None):
        """
        Parameters
        ----------
        data
            DataFrame containing data that should be plotted using heat map
        color_map
            color map to use for coloring the heat map
        min_value
            min possible value (used for adjusting colors on the heatmap)
        max_value
            max possible value (used for adjusting colors on the heatmap)
        start_x
            see: Chart__init__#start_x
        end_x
            see: Chart__init__#end_x
        """
        super().__init__(start_x, end_x)
        self.data = data[::-1]  # for proper plotting the matrix needs to be reversed
        self.color_map = color_map if color_map is not None else mpl.cm.Blues
        self.min_value = min_value
        self.max_value = max_value

        self.color_mesh_ = None
        """ Mesh generated during plotting. """

    def plot(self, figsize=None):
        self._setup_axes_if_necessary(figsize)
        self._draw_heatmap()
        self._set_ticks()
        self._adjust_style()
        self._apply_decorators()

    def _draw_heatmap(self):
        self.color_mesh_ = self.axes.pcolormesh(self.data, cmap=self.color_map,
                                                vmin=self.min_value, vmax=self.max_value)
        self.color_mesh_.update_scalarmappable()  # update info about colors in the mesh

    def _set_ticks(self):
        columns_number = self.data.shape[1]
        rows_number = self.data.shape[0]
        self.axes.xaxis.set_ticks([i + 0.5 for i in range(columns_number)])
        self.axes.yaxis.set_ticks([i + 0.5 for i in range(rows_number)])
