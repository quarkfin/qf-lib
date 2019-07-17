import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.volatility.volatility_manager import VolatilityManager
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

start_date = str_to_date('2014-01-01')
end_date = str_to_date('2016-01-01')

min_lev = 0.2
max_lev = 2


def main():
    data_provider = container.resolve(GeneralPriceProvider)
    series = data_provider.get_price(
        QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date=start_date, end_date=end_date)
    series = series.to_prices(1)

    vol_manager = VolatilityManager(series)
    managed_series, weights_series = vol_manager.get_managed_series(
        vol_level=0.2, window_size=20, lag=1, min_leverage=min_lev, max_leverage=max_lev)
    managed_series = managed_series.to_prices(1)

    line_chart = LineChart()
    series_element = DataElementDecorator(series)
    managed_element = DataElementDecorator(managed_series)

    line_chart.add_decorator(series_element)
    line_chart.add_decorator(managed_element)

    legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
    legend.add_entry(series_element, 'Original')
    legend.add_entry(managed_element, 'Vol_managed')
    line_chart.add_decorator(legend)
    line_chart.plot()
    plt.show(block=True)


if __name__ == '__main__':
    main()
