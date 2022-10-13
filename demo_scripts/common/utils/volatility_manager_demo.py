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
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.volatility.volatility_manager import VolatilityManager
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

start_date = str_to_date('2010-01-01')
end_date = str_to_date('2018-12-31')

min_lev = 0.2
max_lev = 2


def main():
    data_provider = daily_data_provider
    series = data_provider.get_price(DummyTicker('AAA'), PriceField.Close, start_date=start_date, end_date=end_date)
    series = series.to_prices(1)

    vol_manager = VolatilityManager(series)
    managed_series, weights_series = vol_manager.get_managed_series(
        vol_level=0.2, window_size=20, lag=1, min_leverage=min_lev, max_leverage=max_lev)
    managed_series = managed_series.to_prices(1)

    line_chart = LineChart()
    series_element = DataElementDecorator(series)
    managed_element = DataElementDecorator(managed_series)

    line_chart.add_decorator(series_element)
    line_chart.add_decorator(managed_element)

    legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
    legend.add_entry(series_element, 'Original')
    legend.add_entry(managed_element, 'Vol_managed')
    line_chart.add_decorator(legend)
    line_chart.plot()
    plt.show(block=True)


if __name__ == '__main__':
    main()
