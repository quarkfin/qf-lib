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

import seaborn as sns
from matplotlib import cm

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class ReturnsHeatmapChart(Chart):
    """
    Constructs a new monthly returns heatmap chart based on the specified returns.

    Parameters
    ----------
    returns: QFSeries
        series of daily, weekly or monthly data
    """

    def __init__(self, returns: QFSeries, title='Monthly Returns'):
        super().__init__()
        self._returns = returns
        self.title = title

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)

        ret_table = get_aggregate_returns(self._returns, Frequency.MONTHLY, multi_index=True).unstack().round(3)
        ret_table = ret_table.sort_index(ascending=False, axis=0)  # show most recent year at the top
        ret_table = ret_table.fillna(0) * 100
        ret_table.rename(columns={1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}, inplace=True)

        # Format Y axis to make sure we have a tick for each year or 2 years if there is more that 10 years
        year_step = 1
        if len(ret_table.index) > 10:
            year_step = 2

        sns.heatmap(
            ret_table,
            annot=True,
            annot_kws={"size": 6},
            alpha=1.0,
            center=0.0,
            cbar=False,
            cmap=cm.Blues,
            fmt=".1f",
            ax=self.axes,
            yticklabels=year_step  # use the column names but plot only every year_step label.
        )
        self._adjust_style()
        self.axes.yaxis.set_tick_params(rotation=0)

        self.axes.set_xlabel('Month')
        self.axes.set_ylabel('Year')
        self.axes.set_title(self.title)
