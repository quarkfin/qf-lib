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

from itertools import cycle
from typing import List, Any, Tuple

from qf_lib.common.enums.orientation import Orientation
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.helpers.index_translator import IndexTranslator


class BarChart(Chart):
    """
    Creates a new bar chart with the specified ``orientation``.

    Parameters
    ----------
    orientation: Orientation
       The orientation of the bar chart, either Horizontal or Vertical.
    stacked: bool
       default: True; if True then bars corresponding to different DataElementDecorators will be stacked.
       Otherwise bars will be plotted next to each other.
    index_translator: IndexTranslator
       the mapper of index coordinates (e.g. you may use labels as index in a pandas series and this translator
       will ensure that it is plotted correctly)
    thickness: float
       how thick should each bar be (expressed in numeric data coordinates system)
    start_x: datetime.datetime
       The date where the x-axis should begin.
    end_x: datetime.datetime
       The date where the x-axis should end.
    upper_y: float
       The upper bound of the y-axis.
    lower_y: float
       The lower bound of the y-axis.
    plot_settings
       Keyword arguments to pass to the ``plot`` function.
    """

    def __init__(self, orientation: Orientation, stacked: bool = True, index_translator: IndexTranslator = None,
                 thickness: float = 0.8, start_x: Any = None, end_x: Any = None,
                 upper_y: float = None, lower_y: float = None, **plot_settings):
        Chart.__init__(self, start_x, end_x, upper_y, lower_y)

        self.index_translator = index_translator
        self._orientation = orientation
        self._stacked = stacked
        self._thickness = thickness
        self._plot_settings = plot_settings

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)

        self._draw_central_axis()
        self._apply_decorators()
        self._adjust_style()
        IndexTranslator.setup_ticks_and_labels(self)

    def _draw_central_axis(self):
        if self._orientation == Orientation.Horizontal:
            self.axes.axvline(0.0, color='black', linewidth=1)  # vertical line at x=0
        else:
            self.axes.axhline(0.0, color='black', linewidth=1)  # horizontal line at y=0

    def apply_data_element_decorators(self, data_element_decorators: List[DataElementDecorator]) -> Any:
        default_colors = Chart.get_axes_colors()
        default_color_iter = cycle(default_colors)

        # Holds the positions of the bars that have been plotted most recently. It is used to stack
        # bars on top of each other and tracks where to place the bars so that they are on top of each other.
        last_data_element_positions = (None, None)  # (Positive, Negative)

        for data_element in data_element_decorators:
            # copy the general plot settings and add DataElementDecorator-specific plot settings to the copy
            # (overwrite general plot settings if necessary)
            plot_settings = dict(self._plot_settings)
            plot_settings.update(data_element.plot_settings)

            # set color for the bars if it's not specified
            if "color" not in plot_settings:
                plot_settings["color"] = next(default_color_iter)

            data = self._trim_data(data_element.data)

            # Pick the axes to plot on.
            axes = self.axes
            if data_element.use_secondary_axes:
                self.setup_secondary_axes_if_necessary()
                axes = self.secondary_axes

            bars = self._plot_data(axes, data, last_data_element_positions, plot_settings)
            data_element.legend_artist = bars

            last_data_element_positions = self._calculate_last_data_positions(data, last_data_element_positions)

    def _calculate_last_data_positions(self, data, last_data_element_positions):
        positive_positions = None
        negative_positions = None
        if self._stacked:
            positive_positions = data[data >= 0].reindex(data.index, fill_value=0)
            negative_positions = data[data < 0].reindex(data.index, fill_value=0)
            if last_data_element_positions[0] is not None:
                positive_positions += last_data_element_positions[0]

            if last_data_element_positions[1] is not None:
                negative_positions += last_data_element_positions[1]

        return positive_positions, negative_positions

    def _plot_data(self, axes, data, last_data_element_positions, plot_settings):
        index = self.index_translator.translate(data.index) if self.index_translator is not None else data.index

        # Positive and negative values need to be separated in order to plot them accurately when bars are stacked.
        positive = data[data >= 0].reindex(data.index, fill_value=0)
        positive_bars = self._plot_bars(axes, positive, index, last_data_element_positions[0], plot_settings)

        negative = data[data < 0].reindex(data.index, fill_value=0)
        negative_bars = self._plot_bars(axes, negative, index, last_data_element_positions[1], plot_settings)

        return negative_bars if positive_bars is None else positive_bars

    def _plot_bars(self, axes, data, index, last_positions, plot_settings):
        bars = None
        if len(data) > 0:
            if self._orientation == Orientation.Vertical:
                # The bottom parameter specifies the y coordinate of where each bar should start (it's a list of values)
                bars = axes.bar(index, data, bottom=last_positions, width=self._thickness, **plot_settings)
            else:
                # The left parameter specifies the x coordinate of where each bar should start (it's a list of values)
                bars = axes.barh(index, data, left=last_positions, height=self._thickness, **plot_settings)
        return bars

    def _trim_data(self, data):
        # do not trim data using index as it does not make sense for bar chart
        # default behaviour of this function in Chart might cause data removal.
        return data
