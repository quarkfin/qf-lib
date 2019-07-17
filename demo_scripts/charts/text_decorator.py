from datetime import datetime

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.coordinate import DataCoordinate, AxesCoordinate
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.text_decorator import TextDecorator

start_date = str_to_date('1996-01-01')
end_date = datetime.now()
live_start_date = str_to_date('2012-01-01')


def main():
    data_provider = container.resolve(GeneralPriceProvider)
    prices_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)

    line_chart = LineChart()
    data_element = DataElementDecorator(prices_tms)
    line_chart.add_decorator(data_element)

    sample_date = str_to_date('2008-06-01')

    # if you want to test FigureCoordinates, you may want to pass additional argument: clip_on=False
    text_decorator = TextDecorator("Sample text", x=DataCoordinate(sample_date), y=AxesCoordinate(0.9))
    line_chart.add_decorator(text_decorator)

    line_chart.plot()
    plt.show(block=True)


if __name__ == '__main__':
    main()
