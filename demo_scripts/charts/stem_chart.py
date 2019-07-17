import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.stem_decorator import StemDecorator

start_date = str_to_date('2016-07-01')
end_date = str_to_date('2016-08-01')


def main():
    data_provider = container.resolve(GeneralPriceProvider)
    prices_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)

    # add data to the chart and the legend
    marker_props = {'alpha': 0.5}
    stemline_props = {'linestyle': '-.', 'linewidth': 0.2}
    baseline_props = {'visible': False}
    color = 'red'
    marker_props['markeredgecolor'] = color
    marker_props['markerfacecolor'] = color
    stemline_props['color'] = color

    data_elem = StemDecorator(
        prices_tms, marker_props=marker_props, stemline_props=stemline_props, baseline_props=baseline_props)

    line_chart = LineChart()
    line_chart.add_decorator(data_elem)
    line_chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
