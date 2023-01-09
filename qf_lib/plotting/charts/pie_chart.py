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
from typing import Tuple

import numpy as np

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class PieChart(Chart):
    """
    Pie chart util class, it can plot only QFSeries.

    Parameters
    ----------
    data: QFSeries
        The series to plot in the pie chart.
    slices_distance: float
        The distance between slices. Default is 0.01
    start_x: Any
        if not set to None, the chart x-axis will begin at the specified ``start_x`` value
    end_x: Any
        if not set to None, the chart x-axis will end at the specified ``end_x`` value.
    upper_y: Any
       the upper bound of the y-axis.
    lower_y: Any
       the lower bound of the y-axis.
   plot_settings
        Options to pass to the ``pie`` function.
    """

    def __init__(self, data: QFSeries, slices_distance: float = 0.01, start_x: any = None, end_x: any = None, upper_y: any = None, lower_y: any = None, **plot_settings):
        super().__init__(start_x, end_x, upper_y, lower_y)
        self.plot_settings = plot_settings

        self.distance = slices_distance

        self.assert_is_qfseries(data)
        self.data = data.sort_values(ascending=False)

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)

        plot_kwargs = self.plot_settings
        separate = tuple(self.distance for i in range(0, len(self.data)))
        wedges, _ = self.axes.pie(self.data, startangle=90, counterclock=False, explode=separate, **plot_kwargs)
        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-", color='black'),
                  bbox=bbox_props, zorder=0, va="center")

        sum_series = self.data.sum()
        labels = [f"{index}, {value/sum_series:.1%}" for index, value in self.data.iteritems()]

        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            self.axes.annotate(labels[i], xy=(x, y), xytext=(1.2 * np.sign(x), 1.2 * y),
                               horizontalalignment=horizontalalignment, **kw)
        self._apply_decorators()
        self._adjust_style()
