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

from collections import Sequence
from typing import Tuple, Union, Any
from scipy.stats import norm

from qf_lib.plotting.charts.chart import Chart


class HistogramChart(Chart):
    """
    Constructs a new histogram based on the ``series`` specified.

    Parameters
    ----------
    series: Sequence
        The series to plot in the histogram.
    best_fit: boolean, default ``False``.
        Whether a best fit line should be drawn.
    bins: int, str
        The amount of intervals to use for this histogram.
    start_x: Any
       The upper bound of the x-axis.
    end_x: Any
       The lower bound of the x-axis.
    plot_settings
        Options to pass to the ``hist`` function.
    """
    def __init__(self, series: Sequence, best_fit: bool = False, bins: Union[int, str] = 20, start_x: Any = None,
                 end_x: Any = None, **plot_settings):
        super().__init__(start_x=start_x, end_x=end_x)
        self.series = series
        self.plot_settings = plot_settings
        self._num_of_bins = bins
        self._best_fit = best_fit

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)
        # Plot the horizontal bar chart.
        n, bins, patches = self.axes.hist(self.series, bins=self._num_of_bins, ec='white', **self.plot_settings)

        if self._best_fit:
            # Calculate the best fit for the data.
            mu, sigma = norm.fit(self.series)
            # Draw best fit line.
            y = norm.pdf(bins, mu, sigma)
            # Multiply by count of data and bin width to get unnormalised best fit line.
            unnormalised_y = y * len(self.series) * abs(bins[0] - bins[1])
            self.axes.plot(bins, unnormalised_y, "r--")

        # Draw vertical line at x=0.
        self.axes.axvline(0.0, color='black', linewidth=1)

        self._apply_decorators()
        self._adjust_style()
