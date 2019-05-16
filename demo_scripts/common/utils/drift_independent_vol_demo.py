from datetime import datetime

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.volatility.drift_independent_volatility import DriftIndependentVolatility
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator

start_date = str_to_date('2016-01-01')
end_date = datetime.now()

data_provider = container.resolve(GeneralPriceProvider)
ticker = QuandlTicker('AAPL', 'WIKI')
fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]
prices_df = data_provider.get_price(ticker, fields, start_date, end_date)

vol = DriftIndependentVolatility.get_volatility(prices_df, Frequency.DAILY)
print("drift_independent_vol = {}".format(vol))

close_price_tms = prices_df[PriceField.Close]
simple_vol = get_volatility(close_price_tms, Frequency.DAILY)
print("simple_vol = {}".format(simple_vol))

########################################################################################################################

print('\n\n\t--- Drift Independent Volatility Test in progress ---')

ticker = QuandlTicker('MSFT', 'WIKI')
fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]
prices_df = data_provider.get_price(ticker, fields, start_date, end_date)  # type: PricesDataFrame


def simple_vol(close_tms):
    return get_volatility(close_tms, Frequency.DAILY)


def di_vol(prices_df):
    return DriftIndependentVolatility.get_volatility(prices_df, Frequency.DAILY)

window_len = 128

close_price_tms = prices_df[PriceField.Close]  # type: PricesSeries
simple_vols = close_price_tms.rolling_window(window_len, simple_vol)
drift_independent_vols = prices_df.rolling_time_window(window_len, 1, di_vol)

print('Drift Independent Volatility - start value:', drift_independent_vols[0])
print('Simple Volatility - start value:', simple_vols[0])

line_chart = LineChart()
sv_data = DataElementDecorator(simple_vols)
line_chart.add_decorator(sv_data)
div_data = DataElementDecorator(drift_independent_vols)
line_chart.add_decorator(div_data)
line_chart.plot()
print('\nPlot generated successfully.')
plt.show(block=True)