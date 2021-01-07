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

import matplotlib.pyplot as plt
import pandas as pd

from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.stem_decorator import StemDecorator

dates_span = 200
num_of_regressors = 5


def main():
    # GENERATE DATA
    regressors_and_fund_df = QFDataFrame(data=[
        [1, 3, 5],
        [2, 3, 1],
        [3, 1, 2],
        [4, 2, 3],
        [5, 3, 4]
    ],
        index=pd.bdate_range(start='2015-01-01', periods=5),
        columns=['a', 'b', 'c']
    )

    # add data to the chart and the legend
    marker_props_template = {'alpha': 0.5}
    stemline_props_template = {'linestyle': '-.', 'linewidth': 0.2}
    baseline_props = {'visible': True}

    colors = cycle(Chart.get_axes_colors())
    chart = LineChart(start_x=str_to_date('2014-12-31'), end_x=str_to_date('2015-01-08'))
    legend = LegendDecorator()

    for name, series in regressors_and_fund_df.iteritems():
        marker_props = marker_props_template.copy()
        stemline_props = stemline_props_template.copy()

        color = next(colors)
        marker_props['markeredgecolor'] = color
        marker_props['markerfacecolor'] = color
        stemline_props['color'] = color
        data_elem = StemDecorator(series, marker_props=marker_props, stemline_props=stemline_props,
                                  baseline_props=baseline_props)
        chart.add_decorator(data_elem)
        legend.add_entry(data_elem, name)

    chart.add_decorator(legend)
    chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
