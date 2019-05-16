import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator

data_provider = container.resolve(GeneralPriceProvider)
start_date = str_to_date('1996-01-01')
end_date = str_to_date('2014-01-01')

tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date, end_date)
tms2 = data_provider.get_price(QuandlTicker('MSFT', 'WIKI'), PriceField.Close, start_date, end_date)

line_chart = LineChart()
data_element = DataElementDecorator(tms)
line_chart.add_decorator(data_element)

data_element2 = DataElementDecorator(tms2, use_secondary_axes=True)
line_chart.add_decorator(data_element2)

axes_decorator = AxesLabelDecorator(x_label='dates', y_label='primary', secondary_y_label='secondary')
line_chart.add_decorator(axes_decorator)

legend = LegendDecorator(legend_placement=Location.BEST)
legend.add_entry(data_element, 'AAPL')
legend.add_entry(data_element2, 'MSFT')
line_chart.add_decorator(legend)

line_chart.plot()
plt.show(block=True)
