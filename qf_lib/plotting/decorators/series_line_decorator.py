from typing import Any

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class SeriesLineDecorator(ChartDecorator, SimpleLegendItem):
    """
    A simple decorator that displays a single series, useful for charts that want a line overlay for example bar chart.
    """

    def __init__(self, series: QFSeries, key: str = None, use_secondary_axes: bool = False, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self._series = series
        self.use_secondary_axes = use_secondary_axes
        self.plot_settings = plot_settings

    def decorate(self, chart):
        axes = chart.axes
        if self.use_secondary_axes:
            chart.setup_secondary_axes_if_necessary()
            axes = chart.secondary_axes

        self.legend_artist = axes.plot(self._series, **self.plot_settings)[0]
