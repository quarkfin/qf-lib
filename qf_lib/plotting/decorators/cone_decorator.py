#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from datetime import datetime
from typing import Union, Sequence

from qf_lib.common.utils.confidence_interval.analytical_cone import AnalyticalCone
from qf_lib.containers.series.prices_series import PricesSeries, QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class ConeDecorator(ChartDecorator):
    """
    Puts cone on top of the timeseries starting from given date.

    Parameters
    ----------
    series: QFSeries
        series that is going to be decorated by the cone
    live_start_date: datetime
        start date of the cone
    cone_stds: Sequence[Union[float, int], float, int
        defines the size of the cones in standard deviations
    colors_alpha: float
        sets the level of transparency of the cone
    key: str
        see ChartDecorator.key.__init__#key
    """
    def __init__(self, series: QFSeries, live_start_date: datetime,
                 cone_stds: Union[Sequence[Union[float, int]], float, int] = (1, 2),
                 colors_alpha: float = 0.25, key: str = None):
        super().__init__(key)
        self._live_start_date = live_start_date

        assert isinstance(series, PricesSeries), f"Cone can only work with PricesSeries. {type(series)} is not supported"
        self.series = series

        if isinstance(cone_stds, (float, int)):
            cone_stds = [cone_stds]

        assert cone_stds, "cone_stds can't be empty"
        self._cone_stds = cone_stds
        self._colors_alpha = colors_alpha

    def decorate(self, chart: "Chart") -> None:
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
