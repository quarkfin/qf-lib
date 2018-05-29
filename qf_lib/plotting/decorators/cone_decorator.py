from datetime import datetime
from typing import Union, Sequence

from qf_lib.common.utils.returns.analytical_cone import AnalyticalCone
from qf_lib.containers.series.prices_series import PricesSeries, QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class ConeDecorator(ChartDecorator):

    def __init__(self, series: QFSeries, live_start_date: datetime,
                 cone_stds: Union[Sequence[Union[float, int]], float, int]=(1, 2),
                 colors_alpha: float=0.25, key: str=None):
        """
        Puts cone on top of the timeseries starting form given date.

        Parameters
        ----------
        series
            series that is going to be decorated by the cone
        live_start_date
            start date of the cone
        cone_stds
            defines the size of the cones in standard deviations
        colors_alpha
            sets the level of transparency of the cone
        key
            see ChartDecorator.key.__init__#key
        """
        super().__init__(key)
        self._live_start_date = live_start_date

        assert isinstance(series, PricesSeries),\
            "Cone can only work with PricesSeries. {} is not supported" % type(series)
        self.series = series

        if isinstance(cone_stds, (float, int)):
            cone_stds = [cone_stds]

        assert cone_stds, "cone_stds can't be empty"
        self._cone_stds = cone_stds
        self._colors_alpha = colors_alpha

    def decorate(self, chart) -> None:
        prices_tms = self.series
        cone = AnalyticalCone(prices_tms)
        ax = chart.axes

        colors = Chart.get_axes_colors()
        mean_tms = cone.calculate_simple_cone(self._live_start_date, 0)
        ax.plot(mean_tms, color=colors[1])

        for cone_std in self._cone_stds:
            upper_bound_tms = cone.calculate_simple_cone(self._live_start_date, cone_std)
            lower_bound_tms = cone.calculate_simple_cone(self._live_start_date, -cone_std)
            ax.fill_between(upper_bound_tms.index, upper_bound_tms, lower_bound_tms, alpha=self._colors_alpha)
