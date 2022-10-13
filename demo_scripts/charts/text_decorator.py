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

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.coordinate import DataCoordinate, AxesCoordinate
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.text_decorator import TextDecorator

start_date = str_to_date('2006-01-01')
end_date = str_to_date('2018-12-31')
live_start_date = str_to_date('2016-01-01')


def main():
    data_provider = daily_data_provider
    prices_tms = data_provider.get_price(DummyTicker('AAA'), PriceField.Close, start_date, end_date)

    line_chart = LineChart()
    data_element = DataElementDecorator(prices_tms)
    line_chart.add_decorator(data_element)

    sample_date = str_to_date('2008-06-01')

    # if you want to test FigureCoordinates, you may want to pass additional argument: clip_on=False
    text_decorator = TextDecorator("Sample text added to chart", x=DataCoordinate(sample_date), y=AxesCoordinate(0.9))
    line_chart.add_decorator(text_decorator)

    line_chart.plot()
    plt.show(block=True)


if __name__ == '__main__':
    main()
