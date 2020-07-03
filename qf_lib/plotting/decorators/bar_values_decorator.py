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

import matplotlib as mpl

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class BarValuesDecorator(ChartDecorator):
    """
    Adds values next to each bar on the bar chart.

    Parameters
    ----------
    series: QFSeries
        series that is going to be decorated by the cone
    key: str
        see ChartDecorator.key.__init__#key

    """

    def __init__(self, series: QFSeries, key: str = None):
        super().__init__(key)
        self.series = series

    def decorate(self, chart: "Chart") -> None:
        font_size = mpl.rcParams['legend.fontsize']
        max_val = self.series.abs().max()
        space = max_val * 0.02
        for i, v in self.series.iteritems():
            if v < 0:
                x = space
            else:
                x = v + space

            chart.axes.text(x, i, '{:0.1%}'.format(v), verticalalignment='center', size=font_size)

        # move the right limit of the x axis because some labels might go beyond the chart
        _, x_max = chart.axes.get_xlim()
        chart.axes.set_xlim(right=x_max + 7 * space)
