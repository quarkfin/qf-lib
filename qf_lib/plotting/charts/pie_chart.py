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
    plot_settings
        Options to pass to the ``pie`` function.
    """

    def __init__(self, data: QFSeries, slices_distance: float = 0.01, **plot_settings):
        super().__init__()
        self.plot_settings = plot_settings

        self.distance = slices_distance

        self.assert_is_qfseries(data)
        self.data = data.sort_values(ascending=False)

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)

        plot_kwargs = self.plot_settings
        separate = ((self.distance, ) * len(self.data))
        wedges, _ = self.axes.pie(self.data, startangle=90, counterclock=False, explode=separate, **plot_kwargs)

        arrow_props = {
            'arrowstyle': '-',
            'color': 'black'
        }
        bbox_props = {
            "boxstyle": "square,pad=0.3",
            "fc": "w",
            "ec": "k",
            "lw": 0.72
        }
        kw = {
            'arrowprops': arrow_props,
            'bbox': bbox_props,
            'zorder': 0,
            'va': 'center'
        }

        sum_series = self.data.sum()
        labels = [f"{index}, {value / sum_series:.1%}" for index, value in self.data.iteritems()]

        for i, p in enumerate(wedges):
            angle = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(angle))
            x = np.cos(np.deg2rad(angle))
            yc = np.arcsin(y) / (np.pi / 2)
            connection_style = f"angle,angleA=0,angleB={angle}"

            kw["arrowprops"].update({"connectionstyle": connection_style})
            horizontal_alignment = "right" if x <= 0 else "left"

            self.axes.annotate(labels[i], xy=(0.8 * x, 0.8 * y), xytext=((1.3 + (i % 2) * 0.4) * np.sign(x), 1.4 * yc),
                               horizontalalignment=horizontal_alignment, **kw)

        self._apply_decorators()
        self._adjust_style()
