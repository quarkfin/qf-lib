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
from itertools import chain

import numpy as np

from qf_lib.plotting.decorators.coordinate import DataCoordinate
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.text_decorator import TextDecorator
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class WaterfallChart(Chart):
    def __init__(self, percentage: Optional[bool] = False):
        super().__init__()
        self.total_value = None
        self.cumulative_sum = None
        self.percentage = percentage

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)
        self._configure_axis()
        self._add_text()
        self._apply_decorators()

    def _configure_axis(self):
        data_element_decorators = self.get_data_element_decorators()
        indices = list(chain.from_iterable(d.data.index for d in data_element_decorators))
        self.axes.set_xlim(0, len(indices))
        self.axes.tick_params(axis='both', which='major', labelsize=10)
        self.axes.set_xticks(range(len(indices) + 2))
        self.axes.set_xticklabels(['', *indices, ''])

    def _add_text(self):
        data_element_decorators = self.get_data_element_decorators()
        self.cumulative_sum = np.cumsum(np.concatenate([d.data.values for d in data_element_decorators]))
        for index, value in enumerate([value for data_element in data_element_decorators
                                       for value in data_element.data.items()]):
            y_loc = value[1] if index == 0 or value[0] == self.total_value else self.cumulative_sum[index]
            text = "{:.2f}%".format(value[1]) if self.percentage else value[1]
            self.add_decorator(TextDecorator(text, y=DataCoordinate(y_loc + 0.02),
                                             x=DataCoordinate(index + 1),
                                             verticalalignment='bottom',
                                             horizontalalignment='center',
                                             fontsize=10))

    def _plot_waterfall(self, index, value):
        if index == 0 or value[0] == self.total_value:
            color = '#A6A6A6' if value[0] == self.total_value else '#4472C4' if value[1] > 0 else '#ED7D31'
            bottom = 0
        else:
            color = '#4472C4' if value[1] > 0 else '#ED7D31'
            bottom = self.cumulative_sum[index - 1]

        self.axes.bar(index + 1, value[1], bottom=bottom, color=color)

    def add_total(self, value, title: Optional[str] = "Total"):
        series = QFSeries([value], [title])
        self.add_decorator(DataElementDecorator(series))
        self.total_value = series.index

    def flag_total(self, value):
        self.total_value = value

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        for index, value in enumerate([value for data_element in data_element_decorators
                                       for value in data_element.data.items()]):
            self._plot_waterfall(index, value)
