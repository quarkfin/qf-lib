from datetime import datetime

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.helpers.create_return_quantiles import create_return_quantiles

start_date = str_to_date('1996-01-01')
end_date = datetime.now()
live_start_date = str_to_date('2012-01-01')

data_provider = container.resolve(GeneralPriceProvider)
prices_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)

chart = create_return_quantiles(prices_tms, live_start_date)
chart.plot()

chart = create_return_quantiles(prices_tms)
chart.plot()

chart = create_return_quantiles(prices_tms, end_date)
chart.plot()

plt.show(block=True)
