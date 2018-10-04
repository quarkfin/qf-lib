import matplotlib.pyplot as plt
import pandas as pd

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator

dates_a = pd.date_range('2015-01-01', periods=10, freq='D')
a = QFSeries(data=[1, 2, 3, 4, 5, 4, 3, 2, 1, 4], index=dates_a, name='Series A')

dates_b = pd.date_range('2015-01-08', periods=10, freq='D')
b = QFSeries(data=[3, 2, 3, 4, 5, 4, 3, 2, 1, 2], index=dates_b, name='Series B')

dates_c = pd.date_range('2015-01-05', periods=10, freq='D')
c = QFSeries(data=[4, 2, 3, 4, 5, None, 3, 2, 1, 2], index=dates_c, name='Series C')

abc = pd.concat([a, b, c], axis=1, join='outer')
print(abc)

line_chart = LineChart()
line_chart.add_decorator(DataElementDecorator(abc.iloc[:, 0]))
line_chart.add_decorator(DataElementDecorator(abc.iloc[:, 1]))
line_chart.add_decorator(DataElementDecorator(abc.iloc[:, 2]))
line_chart.plot()

plt.show(block=True)
