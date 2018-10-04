import matplotlib.pyplot as plt

import qf_common.config.ioc as ioc
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.cone_chart import ConeChart

start_date = str_to_date('1996-01-01')
end_date = str_to_date('2014-01-01')
live_start_date = str_to_date('2012-01-01')

data_provider = ioc.container.resolve(GeneralPriceProvider)
spy_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)

cone_chart = ConeChart(data=spy_tms, nr_of_data_points=800, is_end_date=live_start_date)
cone_chart.plot()

plt.show(block=True)
