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

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.coordinate import DataCoordinate
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.text_decorator import TextDecorator
from qf_lib.plotting.charts.chart import Chart


class WaterfallChart(Chart):
    """
    Creates a waterfall chart.

    Parameters
    ----------
    percentage: Optional[bool]
        If True, data will be converted to percentages (e.g. 0.1 to 10%).
    add_total: Optional[bool]
        If True, a column with the total will be included.
    """
    def __init__(self, percentage: Optional[bool] = False, add_total: Optional[bool] = False):
        super().__init__()
        self.cumulative_sum = None
        self.percentage = percentage
        self.add_total = add_total
        self.total_label = "Total"

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)
        self._calculate_cumulative_sum()
        if self.add_total:
            self._add_total()
        self._configure_axis()
        self._add_text()
        self._apply_decorators()

    def _calculate_cumulative_sum(self):
        self.cumulative_sum = np.cumsum([0 if data[0] == self.total_label else data[1]
                                         for d in self.get_data_element_decorators()
                                         for data in d.data.items()])

    def _configure_axis(self):
        data_element_decorators = self.get_data_element_decorators()
        indices = list(chain.from_iterable(d.data.index for d in data_element_decorators))
        self.axes.set_xlim(0, len(indices))
        self.axes.tick_params(axis='both', which='major', labelsize=10)
        self.axes.set_xticks(range(len(indices) + 2))
        self.axes.set_xticklabels(['', *indices, ''])

        if self.percentage:
            self.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter(value_format=".2f")))

        # calculate padding dynamically based on the difference between highest and lowest points of the chart
        # for all parts of the charts to be visible
        padding = (self.cumulative_sum.max() - self.cumulative_sum.min()) * 0.1
        ymin = min(-padding, self.cumulative_sum.min() - padding)
        ymax = max(padding, self.cumulative_sum.max() + padding)
        self.axes.set_ylim(ymin, ymax)

    def _add_text(self):
        data_element_decorators = self.get_data_element_decorators()
        for index, value in enumerate([value for data_element in data_element_decorators
                                       for value in data_element.data.items()]):
            y_loc = value[1] if index == 0 or value[0] == self.total_label else self.cumulative_sum[index]
            text = f"{value[1]:.2%}" if self.percentage else f"{value[1]:.2f}"
            self.add_decorator(TextDecorator(text, y=DataCoordinate(y_loc),
                                             x=DataCoordinate(index + 1),
                                             verticalalignment='bottom',
                                             horizontalalignment='center',
                                             fontsize=10))

    def _add_total(self):
        series = QFSeries([self.cumulative_sum[-1]], [self.total_label])
        self.add_decorator(DataElementDecorator(series))

    def _plot_waterfall(self, index, value):
        if value[0] == self.total_label:
            color = '#A6A6A6'
            bottom = 0
        else:
            color = '#4472C4' if value[1] > 0 else '#ED7D31'
            bottom = self.cumulative_sum[index - 1] if index >= 1 else 0

        self.axes.bar(index + 1, value[1], bottom=bottom, color=color)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        for index, value in enumerate([value for data_element in data_element_decorators
                                       for value in data_element.data.items()]):
            self._plot_waterfall(index, value)
