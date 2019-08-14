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

from typing import Union, Sequence

from qf_lib.common.utils.confidence_interval.analytical_cone_base import AnalyticalConeBase
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class ConeProcessDecorator(ChartDecorator):

    def __init__(self, mean: float, std: float, steps: int, starting_value=1,
                 cone_stds: Union[Sequence[Union[float, int]], float, int]=(1, 2),
                 colors_alpha: float=0.25, key: str=None):
        """
        Puts cone on top of the timeseries starting form given date.

        Parameters
        ----------
        mean
            mean return of the process. expressed in the frequency of samples (not annualised)
        std
            std of returns of the process. expressed in the frequency of samples (not annualised)
        steps:
            length of the cone that we are creating
        starting_value
            corresponds to the starting price of the instrument
        cone_stds
            defines the size of the cones in standard deviations
        colors_alpha
            sets the level of transparency of the cone
        key
            see ChartDecorator.key.__init__#key
        """
        super().__init__(key)

        self._mean = mean
        self._std = std
        self._steps = steps
        self._starting_value = starting_value

        if isinstance(cone_stds, (float, int)):
            cone_stds = [cone_stds]

        assert cone_stds, "cone_stds can't be empty"
        self._cone_stds = cone_stds
        self._colors_alpha = colors_alpha

    def decorate(self, chart) -> None:
        cone = AnalyticalConeBase()
        ax = chart.axes

        colors = Chart.get_axes_colors()
        mean_tms = cone.calculate_simple_cone_for_process(self._mean, self._std, 0, self._steps, self._starting_value)
        ax.plot(mean_tms, color=colors[1])

        for cone_std in self._cone_stds:
            upper_bound_tms = cone.calculate_simple_cone_for_process(
                self._mean, self._std, cone_std, self._steps, self._starting_value)
            lower_bound_tms = cone.calculate_simple_cone_for_process(
                self._mean, self._std, -cone_std, self._steps, self._starting_value)
            ax.fill_between(upper_bound_tms.index, upper_bound_tms, lower_bound_tms, alpha=self._colors_alpha)
