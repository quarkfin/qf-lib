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

import datetime
import matplotlib.pyplot as plt

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from qf_lib.common.enums.orientation import Orientation
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

START_DATE = str_to_date('2018-01-01')
END_DATE = str_to_date('2018-01-31')

TICKERS = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC')]


def create_plot_bar_chart(df: QFDataFrame, stacked=True):
    chart_title = TitleDecorator(f"Bar Chart {START_DATE.date()} - {END_DATE.date()}")
    bar_chart = BarChart(orientation=Orientation.Vertical,
                         stacked=stacked,
                         start_x=START_DATE - datetime.timedelta(days=1),
                         end_x=END_DATE + datetime.timedelta(days=1))
    bar_chart.add_decorator(chart_title)
    legend = LegendDecorator()
    for col in df.columns:
        qf_series = QFSeries(df[col])
        data = DataElementDecorator(qf_series)
        bar_chart.add_decorator(data)
        legend.add_entry(data, col)
    bar_chart.add_decorator(legend)
    axes_label = AxesLabelDecorator(x_label='Date', y_label='Value')
    bar_chart.add_decorator(axes_label)
    return bar_chart


def main():
    df = daily_data_provider.get_price(TICKERS, PriceField.Close, start_date=START_DATE, end_date=END_DATE)

    stacked_bar_chart = create_plot_bar_chart(df, stacked=True)
    stacked_bar_chart.plot()
    plt.show(block=True)

    unstacked_bar_chart = create_plot_bar_chart(df, stacked=False)
    unstacked_bar_chart.plot()
    plt.show(block=True)


if __name__ == '__main__':
    main()
