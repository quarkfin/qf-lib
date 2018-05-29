from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class MovingAverageDecorator(ChartDecorator, SimpleLegendItem):
    def __init__(self, window_size, series, key=None, **plot_settings):
        """
        Creates a new decorator which draws a moving average line.

        Parameters
        ----------
        window_size: int
            window size which will be used to draw moving average line
        series: QFSeries
            series to calculate the moving average line for
        plot_settings: keyword arguments
            additional plot settings for matplotlib
        """
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self.window_size = window_size
        self.series = series
        self.plot_settings = plot_settings

    def decorate(self, chart):
        rolling_series = self.series.rolling_window(self.window_size, lambda x: x.mean(), optimised=True)
        series_handle = chart.axes.plot(rolling_series, **self.plot_settings)[0]
        self.legend_artist = series_handle
