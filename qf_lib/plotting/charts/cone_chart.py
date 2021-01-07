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
from itertools import cycle
from typing import Sequence, List, Tuple

from qf_lib.common.utils.confidence_interval.analytical_cone import AnalyticalCone
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


class ConeChart(Chart):
    """
    Plots a cone chart.

    While using a simple cone (e.g. LineChart with Cone decorator) the results of the evaluation may be very different
    depending on the live_start_date. To be immune to this, ConeChart plots only the ends of simple cones which start
    at 1 periods, 2 periods, ..., n periods before the end of the backtested series. The period length depends
    on the frequency of the data provided for the chart. If it has daily frequency, then the length of one period
    will be 1 day.

    Parameters
    ----------
    data: QFSeries
        data to be plotted using ConeChart
    nr_of_data_points: int
        number of data points for which the cone is evaluated
    is_end_date: datetime
        date fixing the end of the In-Sample period
    cone_opacity: float
        opacity of the cone
    cone_stds: Sequence[float]
        list/tuple of different standard deviations for which cones should be drawn

    """

    def __init__(self, data: QFSeries, nr_of_data_points: int, is_end_date: datetime, cone_opacity: float = 0.3,
                 cone_stds: Sequence[float] = (1.0, 2.0)):
        super().__init__()
        self.nr_of_data_points = nr_of_data_points  # Nr of data points for which the cone is evaluated.
        self.is_end_date = is_end_date
        self.cone_opacity = cone_opacity
        self.cone_stds = cone_stds

        self.assert_is_qfseries(data)
        self.data = data

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)

        cone = AnalyticalCone(self.data)
        cone_data_frame = cone.calculate_aggregated_cone(self.nr_of_data_points, self.is_end_date, 0)

        strategy_tms = cone_data_frame['Strategy']
        mean_tms = cone_data_frame['Expectation']

        ax = self.axes
        ax.plot(strategy_tms)
        ax.plot(mean_tms)

        cone_colors = cycle(Chart.get_axes_colors()[2:4])

        # fill areas for every standard deviation
        for cone_std in self.cone_stds:
            upper_df = cone.calculate_aggregated_cone(self.nr_of_data_points, self.is_end_date, cone_std)
            lower_df = cone.calculate_aggregated_cone(self.nr_of_data_points, self.is_end_date, -cone_std)

            upper_bound = upper_df['Expectation']
            lower_bound = lower_df['Expectation']
            ax.fill_between(
                cone_data_frame.index, lower_bound, upper_bound, color=next(cone_colors), alpha=self.cone_opacity)

        ax.set_xlabel('Observations in the past')
        ax.set_ylabel('Current valuation')
        ax.set_title('Performance vs. Expectation')
        ax.set_xlim(0, self.nr_of_data_points)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        pass
