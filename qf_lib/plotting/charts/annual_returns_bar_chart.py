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

from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.axes_formatter_decorator import PercentageFormatter


class AnnualReturnsBarChart(Chart):
    def __init__(self, strategy_tms):
        super().__init__()
        self.strategy_tms = strategy_tms

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)
        annual_returns_tms = self._prepare_data_to_plot()
        self._plot_data(annual_returns_tms)

    def _prepare_data_to_plot(self):
        simple_returns_tms = self.strategy_tms.to_simple_returns()
        annual_returns_tms = get_aggregate_returns(series=simple_returns_tms, convert_to=Frequency.YEARLY)

        return annual_returns_tms

    def _plot_data(self, annual_returns_tms):
        self.axes.yaxis.set_major_formatter(PercentageFormatter())
        self.axes.yaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10], nbins=20, symmetric=True))

        # plot the line for mean
        mean_annual_return = annual_returns_tms.mean()
        self.axes.axhline(mean_annual_return, color='grey', linestyle='--', alpha=0.7)

        # plot the line for 0Y
        self.axes.axhline(0, color='black', linestyle='-')

        # plot yearly returns as bars
        self.axes.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
        annual_returns_tms.plot(ax=self.axes, kind='bar', alpha=0.7, width=0.8)

        self.axes.set_xlabel('Year')
        self.axes.set_ylabel('Returns')
        self.axes.set_title("Annual Returns")

        mean_label = 'mean={0:.2%}'.format(mean_annual_return)
        self.axes.legend([mean_label], loc='best')

        self._adjust_style()
