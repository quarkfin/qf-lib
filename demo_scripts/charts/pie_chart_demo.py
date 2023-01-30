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
from qf_lib.plotting.charts.pie_chart import PieChart


def demo_with_5_data_points():
    my_series = QFSeries([10, 20, 3, 8.6, 4], ["Example 1", "Example 2", "Example 3", "Example 4", "Example 5"])
    pie_chart = PieChart(my_series)
    pie_chart.plot()
    plt.show(block=True)


def demo_with_15_data_points():
    my_series = QFSeries([10, 20, 3, 8.6, 4,
                          10, 20, 3, 8.6, 4,
                          10, 20, 3, 8.6, 4],
                         ["Example 11", "Example 12", "Example 13", "Example 14", "Example 15",
                          "Example 21", "Example 22", "Example 23", "Example 24", "Example 25",
                          "Example 31", "Example 32", "Example 33", "Example 34", "Example 35"])
    pie_chart = PieChart(my_series)
    pie_chart.plot()
    plt.show(block=True)


def main():
    demo_with_5_data_points()
    demo_with_15_data_points()


if __name__ == '__main__':
    main()
