from matplotlib.ticker import Locator

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesLocatorDecorator(ChartDecorator):
    def __init__(self, x_major: Locator=None, x_minor: Locator=None, y_major: Locator=None,
                 y_minor: Locator=None, key=None):
        """
        Creates a new axes locator decorator that changes how often the tickers in the x and y-axis are displayed.

        See here for a list of valid axes locators: http://matplotlib.org/api/ticker_api.html#tick-locating
        """
        # NOTE: for now there is no point in implementing the support for secondary axes because the ticks' positions
        # for secondary axes are changed anyway (to ensure that the grid lines of both axes are aligned).
        # You can find this applied after all the decorators have been already applied.
        super().__init__(key)
        self._x_major = x_major
        self._x_minor = x_minor
        self._y_major = y_major
        self._y_minor = y_minor

    def decorate(self, chart):
        if self._x_major is not None:
            chart.axes.xaxis.set_major_locator(self._x_major)
        if self._x_minor is not None:
            chart.axes.xaxis.set_minor_locator(self._x_minor)
        if self._y_major is not None:
            chart.axes.yaxis.set_major_locator(self._y_major)
        if self._y_minor is not None:
            chart.axes.yaxis.set_minor_locator(self._y_minor)
