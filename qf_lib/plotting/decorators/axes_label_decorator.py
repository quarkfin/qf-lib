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

from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesLabelDecorator(ChartDecorator):
    """
    Creates a new axes label decorator that shows the specified ``x_label`` and ``y_label`` on the chart.
    """
    def __init__(self, x_label: str = None, y_label: str = None, secondary_y_label: str = None, key: str = None):
        super().__init__(key)
        self._x_label = x_label
        self._y_label = y_label
        self.secondary_y_label = secondary_y_label

    def decorate(self, chart: Chart):
        if self._x_label is not None:
            chart.axes.set_xlabel(self._x_label)
        if self._y_label is not None:
            chart.axes.set_ylabel(self._y_label)
        if self.secondary_y_label is not None:
            chart.secondary_axes.set_ylabel(self.secondary_y_label)
