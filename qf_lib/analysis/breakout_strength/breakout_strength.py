from datetime import datetime

import matplotlib.pyplot as plt

import qf_common.config.ioc as ioc
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

start_date = str_to_date('2010-01-01')
end_date = datetime.now()

data_provider = ioc.container.resolve(GeneralPriceProvider)
prices_df = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.ohlcv(), start_date, end_date) #type: PricesDataFrame





window_len = 128
trend_strength_tms = prices_df.rolling_time_window(window_length=window_len, step=1, func=trend_strength)
down_trend_strength_tms = prices_df.rolling_time_window(window_length=window_len, step=1, func=down_trend_strength)
up_trend_strength_tms = prices_df.rolling_time_window(window_length=window_len, step=1, func=up_trend_strength)

line_chart = LineChart()
price_elem = DataElementDecorator(prices_df[PriceField.Close])
line_chart.add_decorator(price_elem)

trend_elem = DataElementDecorator(trend_strength_tms, use_secondary_axes=True, color='black')
down_trend_elem = DataElementDecorator(down_trend_strength_tms, use_secondary_axes=True)
up_trend_elem = DataElementDecorator(up_trend_strength_tms, use_secondary_axes=True)

line_chart.add_decorator(trend_elem)
line_chart.add_decorator(down_trend_elem)
line_chart.add_decorator(up_trend_elem)

legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
legend.add_entry(price_elem, 'Stock price')
legend.add_entry(trend_elem, 'Trend strength')
legend.add_entry(down_trend_elem, 'Down trend')
legend.add_entry(up_trend_elem, 'Up trend')

line_chart.add_decorator(legend)

line_chart.plot()
plt.show(block=True)
