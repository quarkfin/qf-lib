import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.annual_returns_bar_chart import AnnualReturnsBarChart

start_date = str_to_date('2000-01-01')
end_date = str_to_date('2016-05-29')

data_provider = container.resolve(GeneralPriceProvider)
series = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date=start_date, end_date=end_date)

annual_rets_chart = AnnualReturnsBarChart(series)
annual_rets_chart.plot()

plt.show(block=True)
