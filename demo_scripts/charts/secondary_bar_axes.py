import matplotlib.pyplot as plt

from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.orientation import Orientation
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.series_line_decorator import SeriesLineDecorator

tms = QFSeries(data=[200, 20, 300, 40], index=[1, 2, 3, 4])
tms2 = QFSeries(data=[80, 20, 100, 40], index=[1, 2, 3, 4])
tms3 = QFSeries(data=[80, 20, 100, 40], index=[1, 2, 3, 4])

bar_chart = BarChart(Orientation.Vertical)
data_element = DataElementDecorator(tms)
bar_chart.add_decorator(data_element)

data_element2 = DataElementDecorator(tms2)
bar_chart.add_decorator(data_element2)

bar_chart.add_decorator(SeriesLineDecorator(tms3, use_secondary_axes=True))

legend = LegendDecorator(legend_placement=Location.BEST)
legend.add_entry(data_element, 'Series 1')
legend.add_entry(data_element2, 'Series 2')
bar_chart.add_decorator(legend)

bar_chart.plot()
plt.show(block=True)
