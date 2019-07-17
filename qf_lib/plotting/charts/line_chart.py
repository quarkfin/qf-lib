from itertools import cycle
from typing import List, Tuple

import matplotlib as mpl

from qf_lib.plotting.charts.chart import Chart


class LineChart(Chart):
    """
    Simple line chart. It can plot both QFSeries and DataFrames.
    """

    def __init__(self, start_x: any = None, end_x: any = None, upper_y: any = None, lower_y: any = None,
                 log_scale: bool = False, rotate_x_axis=False):
        """
        Creates a new LineChart instance.

        If ``start_x`` is not None, then the chart x-axis will begin at the specified ``start_x`` value.
        If ``end_x`` is not None, then the chart x-axis will end at the specified ``end_x`` value.
        By default the ``start_x`` and ``end_x`` will be determined by the series added to the chart. So whatever
        the earliest data point is will determine the ``start_x``.
        """
        super().__init__(start_x, end_x, upper_y, lower_y)
        self.log_scale = log_scale
        self._rotate_x_axis = rotate_x_axis

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)

        if self.log_scale:
            self.axes.set_yscale('log')

        self._adjust_style()

        if self._rotate_x_axis:
            self.figure.autofmt_xdate()

        self._apply_decorators()
        self.axes.set_xmargin(0)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        colors = cycle(Chart.get_axes_colors())

        for data_element in data_element_decorators:
            plot_settings = data_element.plot_settings.copy()
            plot_settings.setdefault("color", next(colors))

            series = data_element.data
            trimmed_series = self._trim_data(series)

            axes = self._ax
            if data_element.use_secondary_axes:
                mpl.rcParams['axes.spines.right'] = True  # Ensure that the right axes spine is shown.
                self.setup_secondary_axes_if_necessary()
                axes = self._secondary_axes

            handle = axes.plot(trimmed_series, **plot_settings)[0]
            data_element.legend_artist = handle
