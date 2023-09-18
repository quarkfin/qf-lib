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
from matplotlib import pyplot as plt

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.waterfall_chart import WaterfallChart


def waterfall_demo_without_total():
    my_series = QFSeries([4.55, 5.23, -3.03, 6.75],
                         ['Value 1', 'Value 2', 'Value 3', 'Value 4'])
    pie_chart = WaterfallChart(my_series, title="Waterfall Chart Without Total")

    pie_chart.plot()
    plt.show(block=True)


def waterfall_demo_with_total():
    my_series = QFSeries([4.55, 5.23, -3.03, ],
                         ['Value 1', 'Value 2', 'Value 3'])
    pie_chart = WaterfallChart(my_series, title="Waterfall Chart With Total")
    pie_chart.add_total(6.75, title="Value 4")

    pie_chart.plot()
    plt.show(block=True)


def main():
    waterfall_demo_with_total()
    waterfall_demo_without_total()


if __name__ == '__main__':
    main()
