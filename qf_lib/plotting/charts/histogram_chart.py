from collections import Sequence

import matplotlib.mlab as mlab
from scipy.stats import norm

from qf_lib.plotting.charts.chart import Chart


class HistogramChart(Chart):
    def __init__(self, series: Sequence, best_fit=False, bins=20, **plot_settings):
        """
        Constructs a new histogram based on the ``series`` specified.

        Parameters
        ----------
        series
            The series to plot in the histogram.
        best_fit: boolean, default ``False``.
            Whether a best fit line should be drawn.
        bins: int, default 20.
            The amount of intervals to use for this histogram.
        plot_settings: keyword arguments
            Options to pass to the ``hist`` function.
        """
        super().__init__(start_x=None, end_x=None)
        self._series = series
        self.plot_settings = plot_settings
        self._num_of_bins = bins
        self._best_fit = best_fit

    def plot(self, figsize=None):
        self._setup_axes_if_necessary(figsize)
        # Plot the horizontal bar chart.
        n, bins, patches = self.axes.hist(self._series, bins=self._num_of_bins, ec='white',
                                          **self.plot_settings)

        if self._best_fit:
            # Calculate the best fit for the data.
            mu, sigma = norm.fit(self._series)
            # Draw best fit line.
            y = mlab.normpdf(bins, mu, sigma)
            # Multiply by count of data and bin width to get unnormalised best fit line.
            unnormalised_y = y * len(self._series) * abs(bins[0] - bins[1])
            self.axes.plot(bins, unnormalised_y, "r--")

        # Draw vertical line at x=0.
        self.axes.axvline(0.0, color='black', linewidth=1)

        self._apply_decorators()
        self._adjust_style()
