from itertools import cycle

from qf_lib.common.utils.returns.list_longest_drawdowns import list_longest_drawdowns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class TopDrawdownDecorator(ChartDecorator):
    """
    Highlights the top drawdowns in a specified series.
    """
    def __init__(self, prices: QFSeries, count: int, colors=None, key=None):
        """
        Construct a new TopDrawdownDecorator.

        The top ``count`` amount of drawdowns will be highlighted. If ``colors`` is ``None`` then a default list of
        colours will be used, you can override it by specifying a list of strings containing color names or hex codes.

        Parameters
        ----------
        prices
            A series from which drawdowns will be calculated.
        count
            The amount of longest drawdowns to highlight.
        colors
            A list of colours to use to highlight the drawdowns.
        """
        super().__init__(key)
        if colors is None:
            self._color = Chart.get_axes_colors()[3]
        else:
            self._color = cycle(colors)
        self._current_color = 0

        self._series = prices
        self._count = count

    def decorate(self, chart):

        for drawdown in list_longest_drawdowns(self._series, self._count):
            chart.axes.axvspan(drawdown[0], drawdown[1], alpha=0.2, color=self._color)

