from datetime import datetime
from itertools import cycle
from typing import Sequence

from qf_lib.common.utils.returns.analytical_cone import AnalyticalCone
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class ConeChart(Chart):
    """
    While using a simple cone (e.g. LineChart with Cone decorator) the results of the evaluation may be very different
    depending on the live_start_date. To be immune to this, ConeChart plots only the ends of simple cones which start
    at 1 periods, 2 periods, ..., n periods before the end of the backtested series. The period length depends
    on the frequency of the data provided for the chart. If it has daily frequency, then the length of one period
    will be 1 day.
    """

    def __init__(self, data: QFSeries, nr_of_data_points: int, is_end_date: datetime, cone_opacity: float=0.3,
                 cone_stds: Sequence[float]=(1.0, 2.0)):
        """
        Parameters
        ----------
        data
            data to be plotted using ConeChart
        nr_of_data_points
            number of data points for which the cone is evaluated
        is_end_date
            date fixing the end of the In-Sample period
        cone_opacity
            opacity of the cone
        cone_stds
            list/tuple of different standard deviations for which cones should be drawn
        """
        super().__init__()
        self.nr_of_data_points = nr_of_data_points  # Nr of data points for which the cone is evaluated.
        self.is_end_date = is_end_date
        self.cone_opacity = cone_opacity
        self.cone_stds = cone_stds

        self.assert_is_qfseries(data)
        self.data = data

    def plot(self, figsize=None):
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
            ax.fill_between(cone_data_frame.index, lower_bound, upper_bound,
                            color=next(cone_colors), alpha=self.cone_opacity)

        ax.set_xlabel('Days in the past')
        ax.set_ylabel('Current valuation')
        ax.set_title('Performance vs. Expectation')
        ax.set_xlim(0, self.nr_of_data_points)
