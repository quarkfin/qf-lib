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
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def waterfall_demo_without_total():
    data = DataElementDecorator(QFSeries([4.55, 5.23, -3.03, 6.75],
                                         ['Value 1', 'Value 2', 'Value 3', 'Value 4']))

    chart = WaterfallChart()
    chart.add_decorator(data)

    chart_title = TitleDecorator("Waterfall Chart Without Total")
    chart.add_decorator(chart_title)

    chart.plot()
    plt.show(block=True)


def waterfall_demo_with_total():

    data_element = DataElementDecorator(QFSeries([4.55, 5.23, -3.03],
                                        ['Value 1', 'Value 2', 'Value 3']))

    chart = WaterfallChart()
    chart.add_decorator(data_element)
    chart.add_total(6.75, title="Value 4")

    chart_title = TitleDecorator("Waterfall Chart With Total")
    chart.add_decorator(chart_title)

    chart.plot()
    plt.show(block=True)


def waterfall_demo_flag_total():
    data_element = DataElementDecorator(QFSeries([4.55, 5.23, -3.03, 6.75],
                                                 ['Value 1', 'Value 2', 'Value 3', 'Value 4']))

    chart = WaterfallChart()
    chart.add_decorator(data_element)

    chart.flag_total("Value 4")

    chart_title = TitleDecorator("Waterfall Chart Flagged Total")
    chart.add_decorator(chart_title)

    chart.plot()
    plt.show(block=True)


def waterfall_demo_with_percentage():
    data_element_1 = DataElementDecorator(QFSeries([4.55, 5.23],
                                                   ['Value 1', 'Value 2']))

    data_element_2 = DataElementDecorator(QFSeries([-3.03, 6.75],
                                                   ['Value 3', 'Value 4']))

    chart = WaterfallChart(percentage=True)
    chart.add_decorator(data_element_1)
    chart.add_decorator(data_element_2)

    chart_title = TitleDecorator("Waterfall Chart With Percentage")
    chart.add_decorator(chart_title)

    chart.plot()
    plt.show(block=True)


def main():
    waterfall_demo_without_total()
    waterfall_demo_with_total()
    waterfall_demo_flag_total()
    waterfall_demo_with_percentage()


if __name__ == '__main__':
    main()
