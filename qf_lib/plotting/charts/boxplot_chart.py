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

from typing import List, Tuple

import seaborn as sns

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class BoxplotChart(Chart):
    """
    Creates a box plot consisting of the list of ``QFSeries`` specified in ``data``.

    Parameters
    ----------
    data: List[QFSeries]
       A list of ``QFSeries``.
    plot_settings
       Passed to Seaborn plotting function.
    """

    SERIES_KEY = "series"
    """Used for storing the boxplot chart's series."""

    def __init__(self, data: List[QFSeries], **plot_settings):
        super().__init__(start_x=None, end_x=None)
        self._data = data
        self.plot_settings = plot_settings

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)

        # Seaborn 0.13.2 raises when it receives a list of Series together
        # with a palette. Keep the public qf-lib input unchanged, but pass a
        # qf-lib DataFrame to seaborn so each series remains a separate box.
        plot_data = QFDataFrame({
            index: series.reset_index(drop=True)
            for index, series in enumerate(self._data)
        })
        sns.boxplot(ax=self.axes, data=plot_data, **self.plot_settings)

        self._adjust_style()
        self._apply_decorators()
