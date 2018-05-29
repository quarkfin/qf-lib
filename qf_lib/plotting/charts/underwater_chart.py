from itertools import cycle
from typing import List

from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import PercentageFormatter
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


class UnderwaterChart(LineChart):
    def __init__(self, strategy_tms, rotate_x_axis=False):
        super().__init__(rotate_x_axis=rotate_x_axis)
        self.add_decorator(DataElementDecorator(strategy_tms))

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        colors = cycle(Chart.get_axes_colors())

        for data_element in data_element_decorators:
            plot_settings = data_element.plot_settings.copy()
            plot_settings.setdefault("color", next(colors))

            series = data_element.data
            trimmed_series = self._trim_data(series)
            drawdown_series = drawdown_tms(trimmed_series)
            drawdown_series *= -1

            axes = self._ax
            axes.yaxis.set_major_formatter(PercentageFormatter())
            axes.fill_between(drawdown_series.index, 0, drawdown_series.values)
            axes.set_ylim(top=0)
