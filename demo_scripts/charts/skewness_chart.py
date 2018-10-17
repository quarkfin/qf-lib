from datetime import datetime

import matplotlib.pyplot as plt

import qf_common.config.ioc as ioc
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker, BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.helpers.create_skewness_chart import create_skewness_chart

# ticker = QuandlTicker('AAPL', 'WIKI')
ticker = BloombergTicker('SPX Index')

start_date = str_to_date('1996-01-01')
end_date = datetime.now()

data_provider = ioc.container.resolve(GeneralPriceProvider)
prices_tms = data_provider.get_price(ticker, PriceField.Close, start_date, end_date)

chart = create_skewness_chart(prices_tms)

chart.plot()

plt.show(block=True)
