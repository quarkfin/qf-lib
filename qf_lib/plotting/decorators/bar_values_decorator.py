import matplotlib as mpl

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class BarValuesDecorator(ChartDecorator):
    """
    Adds values next to each bar on the bar chart
    """

    def __init__(self, series: QFSeries, key: str = None):
        """
        Puts cone on top of the timeseries starting form given date.

        Parameters
        ----------
        series
            series that is going to be decorated by the cone
        key
            see ChartDecorator.key.__init__#key
        """
        super().__init__(key)
        self.series = series

    def decorate(self, chart: "Chart") -> None:
        font_size = mpl.rcParams['legend.fontsize']
        max_val = self.series.abs().max()
        space = max_val * 0.02
        for i, v in self.series.iteritems():
            if v < 0:
                x = space
            else:
                x = v + space

            chart.axes.text(x, i, '{:0.1%}'.format(v), verticalalignment='center', size=font_size)

        # move the right limit of the x axis because some labels might go beyond the chart
        _, x_max = chart.axes.get_xlim()
        chart.axes.set_xlim(right=x_max + 7 * space)
