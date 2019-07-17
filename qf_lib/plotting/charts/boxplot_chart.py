from typing import List, Tuple

import seaborn as sns

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class BoxplotChart(Chart):
    SERIES_KEY = "series"  # Used for storing the boxplot chart's series.

    def __init__(self, data: List[QFSeries], **plot_settings):
        """
        Creates a box plot consisting of the list of ``QFSeries`` specified in ``data``.

        Parameters
        ----------
        data
            A list of ``QFSeries``.
        plot_settings
            Passed to Seaborn plotting function.
        """
        super().__init__(start_x=None, end_x=None)
        self._data = data
        self.plot_settings = plot_settings

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)

        plot_kwargs = self.plot_settings

        # Plot the boxes.
        colors = Chart.get_axes_colors()
        sns.boxplot(ax=self.axes, data=self._data, palette=colors, **plot_kwargs)

        self._apply_decorators()
        self._adjust_style()
