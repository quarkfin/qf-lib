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

from plotting.decorators.coordinate import DataCoordinate
from plotting.decorators.text_decorator import TextDecorator
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class WaterfallChart(Chart):
    def __init__(self, data: QFSeries, title: Optional[str] = None, percentage: Optional[bool] = False):
        super().__init__()
        self.total_value = None
        self.cumulative_sum = None
        self.data = data
        self.assert_is_qfseries(data)
        self.title = title
        self.percentage = percentage

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)
        self.axes.set_xlim(0, self.data.size)

        self.cumulative_sum = np.cumsum(self.data.values)
        for index, value in enumerate(self.data.items()):
            self._plot_waterfall(index, value)

        # Set x-axis label using 'category' column
        self.axes.tick_params(axis='both', which='major', labelsize=10)
        self.axes.set_xticks(range(len(self.data.index) + 2))
        self.axes.set_xticklabels(['', *self.data.index, ''])
        self.axes.set_title(self.title, y=1.04)

        self._apply_decorators()

    def _plot_waterfall(self, index, value):
        if index == 0 or value[0] == self.total_value:
            color = '#A6A6A6' if value[0] == self.total_value else '#4472C4' if value[1] > 0 else '#ED7D31'
            bottom = 0
            y_loc = value[1]

        else:
            color = '#4472C4' if value[1] > 0 else '#ED7D31'
            bottom = self.cumulative_sum[index - 1]
            y_loc = self.cumulative_sum[index]

        text = "{:.2f}%".format(value[1]) if self.percentage else value[1]

        self.axes.bar(index + 1, value[1], bottom=bottom, color=color)
        self.add_decorator(TextDecorator(text, y=DataCoordinate(y_loc + 0.02), x=DataCoordinate(index + 1),
                                         verticalalignment='bottom', horizontalalignment='center', fontsize=10))

    def add_total(self, value, title: Optional[str] = "Total"):
        self.data = self.data.append(QFSeries([value], [title]))
        self.total_value = self.data.index[-1]

    def flag_total(self, value):
        self.total_value = value

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        pass
