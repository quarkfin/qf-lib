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

import matplotlib.pyplot as plt
import pandas as pd

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


def main():
    dates_a = pd.date_range('2015-01-01', periods=10, freq='D')
    a = QFSeries(data=[1, 2, 3, 4, 5, 4, 3, 2, 1, 4], index=dates_a, name='Series A')

    dates_b = pd.date_range('2015-01-08', periods=10, freq='D')
    b = QFSeries(data=[3, 2, 3, 4, 5, 4, 3, 2, 1, 2], index=dates_b, name='Series B')

    dates_c = pd.date_range('2015-01-05', periods=10, freq='D')
    c = QFSeries(data=[4, 2, 3, 4, 5, None, 3, 2, 1, 2], index=dates_c, name='Series C')

    abc = pd.concat([a, b, c], axis=1, join='outer')
    print(abc)

    line_chart = LineChart()
    line_chart.add_decorator(DataElementDecorator(abc.iloc[:, 0]))
    line_chart.add_decorator(DataElementDecorator(abc.iloc[:, 1]))
    line_chart.add_decorator(DataElementDecorator(abc.iloc[:, 2]))
    line_chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
