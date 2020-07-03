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
from typing import List, Tuple

import matplotlib as mpl

from qf_lib.plotting.charts.chart import Chart


class LineChart(Chart):
    """
    Simple line chart. It can plot both QFSeries and DataFrames.
    By default the ``start_x`` and ``end_x`` will be determined by the series added to the chart. So whatever
    the earliest data point is will determine the ``start_x``.

    Parameters
    ----------
    start_x: Any
        if not set to None, the chart x-axis will begin at the specified ``start_x`` value
    end_x: Any
        if not set to None, the chart x-axis will end at the specified ``end_x`` value.
    upper_y: Anny
       the upper bound of the y-axis.
    lower_y: Anny
       the lower bound of the y-axis.
    log_scale: bool
        use log scale.
    rotate_x_axis: bool
        rotate the x-axis.
    """
    def __init__(self, start_x: any = None, end_x: any = None, upper_y: any = None, lower_y: any = None,
                 log_scale: bool = False, rotate_x_axis=False):

        super().__init__(start_x, end_x, upper_y, lower_y)
        self.log_scale = log_scale
        self._rotate_x_axis = rotate_x_axis

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)

        if self.log_scale:
            self.axes.set_yscale('log')

        self._adjust_style()

        if self._rotate_x_axis:
            self.figure.autofmt_xdate()

        self._apply_decorators()
        self.axes.set_xmargin(0)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        colors = cycle(Chart.get_axes_colors())

        for data_element in data_element_decorators:
            plot_settings = data_element.plot_settings.copy()
            plot_settings.setdefault("color", next(colors))

            series = data_element.data
            trimmed_series = self._trim_data(series)

            axes = self._ax
            if data_element.use_secondary_axes:
                mpl.rcParams['axes.spines.right'] = True  # Ensure that the right axes spine is shown.
                self.setup_secondary_axes_if_necessary()
                axes = self._secondary_axes

            handle = axes.plot(trimmed_series, **plot_settings)[0]
            data_element.legend_artist = handle
