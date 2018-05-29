from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesLabelDecorator(ChartDecorator):
    def __init__(self, x_label: str=None, y_label: str=None, secondary_y_label: str=None, key=None):
        """
        Creates a new axes label decorator that shows the specified ``x_label`` and ``y_label`` on the chart.
        """
        super().__init__(key)
        self._x_label = x_label
        self._y_label = y_label
        self.secondary_y_label = secondary_y_label

    def decorate(self, chart: Chart):
        if self._x_label is not None:
            chart.axes.set_xlabel(self._x_label)
        if self._y_label is not None:
            chart.axes.set_ylabel(self._y_label)
        if self.secondary_y_label is not None:
            chart.secondary_axes.set_ylabel(self.secondary_y_label)
