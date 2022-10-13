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
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.volatility.drift_independent_volatility import DriftIndependentVolatility
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

start_date = str_to_date('2016-01-01')
end_date = str_to_date('2018-12-31')
ticker = DummyTicker('AAA')


def _calculate_single_values(data_provider):

    fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]
    prices_df = data_provider.get_price(ticker, fields, start_date, end_date)

    di_vol = DriftIndependentVolatility.get_volatility(prices_df, Frequency.DAILY)
    print("drift_independent_vol = {}".format(di_vol))

    close_price_tms = prices_df[PriceField.Close]
    simple_vol = get_volatility(close_price_tms, Frequency.DAILY)
    print("simple_vol = {}".format(simple_vol))


def _calculate_timeseries(data_provider):
    print('\n\n\t--- Drift Independent Volatility Test in progress ---')

    def simple_vol(close_tms):
        return get_volatility(close_tms, Frequency.DAILY)

    def di_vol(ohlc_df):
        return DriftIndependentVolatility.get_volatility(ohlc_df, Frequency.DAILY)

    fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]
    prices_df = data_provider.get_price(ticker, fields, start_date, end_date)  # type: PricesDataFrame

    window_len = 128

    close_price_tms = prices_df[PriceField.Close]  # type: PricesSeries
    simple_vols = close_price_tms.rolling_window(window_len, simple_vol)
    print('Simple Volatility - start value:', simple_vols[0])

    drift_independent_vols = prices_df.rolling_time_window(window_len, 1, di_vol)
    print('Drift Independent Volatility - start value:', drift_independent_vols[0])

    line_chart = LineChart()
    sv_data = DataElementDecorator(simple_vols)
    line_chart.add_decorator(sv_data)

    div_data = DataElementDecorator(drift_independent_vols)
    line_chart.add_decorator(div_data)

    legend = LegendDecorator(legend_placement=Location.BEST)
    legend.add_entry(sv_data, 'Simple Volatility')
    legend.add_entry(div_data, 'Drift independent Volatility')
    line_chart.add_decorator(legend)

    line_chart.plot()
    print('\nPlot generated successfully.')
    plt.show(block=True)


def main():
    data_provider = daily_data_provider

    _calculate_single_values(data_provider)
    _calculate_timeseries(data_provider)


if __name__ == '__main__':
    main()
