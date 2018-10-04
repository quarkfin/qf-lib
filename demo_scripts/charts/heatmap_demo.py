import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qf_lib.common.enums.axis import Axis
from qf_lib.plotting.charts.heatmap.color_bar import ColorBar
from qf_lib.plotting.charts.heatmap.heatmap_chart import HeatMapChart
from qf_lib.plotting.charts.heatmap.values_annotations import ValuesAnnotations
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator

sample_values = np.random.rand(4, 5) * 2 - 1
rows = ['aaaa', 'bbbbbb', 'ccccc', 'ddddddddddd']
cols = ['a', 'b', 'c', 'd', 'e']

sample_df = pd.DataFrame(data=sample_values, index=pd.Index(rows), columns=pd.Index(cols))
chart = HeatMapChart(data=sample_df, min_value=-1, max_value=1)

chart.add_decorator(AxisTickLabelsDecorator(labels=cols, axis=Axis.X, rotation='vertical'))
chart.add_decorator(AxisTickLabelsDecorator(labels=reversed(rows), axis=Axis.Y))
chart.add_decorator(ValuesAnnotations())
chart.add_decorator(ColorBar())

chart.plot()
chart.figure.tight_layout()
plt.show(block=True)
