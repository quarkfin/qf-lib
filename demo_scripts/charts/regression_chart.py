import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.regression_chart import RegressionChart

start_date = str_to_date('2014-01-01')
end_date = str_to_date('2018-01-01')

data_provider = container.resolve(GeneralPriceProvider)
benchmark_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)
strategy_tms = data_provider.get_price(QuandlTicker('MSFT', 'WIKI'), PriceField.Close, start_date, end_date)

regression_chart = RegressionChart(benchmark_tms=benchmark_tms, strategy_tms=strategy_tms)
regression_chart.plot()

plt.show(block=True)
