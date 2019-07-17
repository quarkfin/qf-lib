from datetime import datetime

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.cone_decorator import ConeDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

start_date = str_to_date('2016-01-01')
end_date = datetime.now()
live_start_date = str_to_date('2017-05-01')


def main():
    data_provider = container.resolve(GeneralPriceProvider)
    prices_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)

    line_chart = LineChart()
    data_element = DataElementDecorator(prices_tms)
    line_chart.add_decorator(data_element)
    legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
    legend.add_entry(data_element, 'SPY')
    line_chart.add_decorator(legend)

    cone_decorator = ConeDecorator(live_start_date=live_start_date, series=prices_tms, key='cone')
    line_chart.add_decorator(cone_decorator)
    line_chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
