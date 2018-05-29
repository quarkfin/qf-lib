from qf_lib.plotting.charts.heatmap.heatmap_chart_decorator import HeatMapChartDecorator


class ColorBar(HeatMapChartDecorator):
    """ Adds color bar to the heat map. """

    def __init__(self, key=None, **plot_settings):
        super().__init__(key)
        self._color_bar = None
        self._plot_settings = plot_settings

    def decorate(self, chart: "HeatMapChart"):
        self._color_bar = chart.axes.figure.colorbar(chart.color_mesh_, ax=chart.axes, **self._plot_settings)
