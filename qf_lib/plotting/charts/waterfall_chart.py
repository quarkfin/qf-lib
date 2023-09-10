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
from typing import Tuple, Optional, List

import numpy as np

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class WaterfallChart(Chart):
    def __init__(self, data: QFSeries, title: Optional[str] = None, total: Optional[List] = None):
        super().__init__()
        self.cumulative_sum = None
        self.data = data
        self.assert_is_qfseries(data)
        self.title = title
        self.total = total

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)
        self.axes.set_xlim(0, self.data.size)

        self.cumulative_sum = np.cumsum(self.data.values)
        for index, value in enumerate(self.data.items()):
            self._plot_waterfall(index, value)

        # Set x-axis label using 'category' column
        self.axes.set_xticks(range(len(self.data.index) + 2))
        self.axes.set_xticklabels(['', *self.data.index, ''])

    def _plot_waterfall(self, index, value):

        # Bar color is determined based on whether there has been an increase, decrease,
        # or it represents a total column.
        color = '#A6A6A6' if value[0] in self.total else '#4472C4' if value[1] > 0 else '#ED7D31'

        if index == 0 or value[0] in self.total:
            self.axes.bar(index + 1, value[1], color=color)
        else:
            self.axes.bar(index + 1, value[1], bottom=self.cumulative_sum[index - 1], color=color)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        pass
