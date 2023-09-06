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

from plotting.charts.waterfall_chart import WaterfallChart
from qf_lib.containers.series.qf_series import QFSeries


def waterfall_demo():
    my_series = QFSeries([4.42, 4.60, -3.55, 5.47],
                         ['FX Un-Hedged Performance', 'CHFUSD Move', 'Cost of hedging', 'FX Hedged Performance'])
    pie_chart = WaterfallChart(my_series, title="Waterfall Chart", total=['FX Hedged Performance'])
    pie_chart.plot()
    plt.show(block=True)


def main():
    waterfall_demo()


if __name__ == '__main__':
    main()