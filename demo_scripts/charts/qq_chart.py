from datetime import datetime

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.helpers.create_qq_chart import create_qq_chart

start_date = str_to_date('2005-01-01')
end_date = datetime.now()


def main():
    data_provider = container.resolve(GeneralPriceProvider)

    prices_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)

    chart = create_qq_chart(prices_tms)
    chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
