from typing import Any

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class MovingAverageDecorator(ChartDecorator, SimpleLegendItem):
    def __init__(self, window_size: int, series: QFSeries, key: str = None, **plot_settings: Any):
        """
        Creates a new decorator which draws a moving average line.

        Parameters
        ----------
        window_size
            window size which will be used to draw moving average line
        series
            series to calculate the moving average line for
        plot_settings
            additional plot settings for matplotlib
        """
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self.window_size = window_size
        self.series = series
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart"):
        rolling_series = self.series.rolling_window(self.window_size, lambda x: x.mean(), optimised=True)
        series_handle = chart.axes.plot(rolling_series, **self.plot_settings)[0]
        self.legend_artist = series_handle
