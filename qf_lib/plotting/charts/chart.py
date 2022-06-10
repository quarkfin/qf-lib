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

import base64
import datetime
import io
import threading
import urllib.parse
import uuid
from collections import OrderedDict
from typing import List, Any, Union, Tuple

import matplotlib as mpl
import matplotlib.artist as artist
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.ticker import FixedLocator

from qf_lib.common.enums.orientation import Orientation
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import ChartDecorator


class Chart:
    """
    Abstract class for all the charts.

    Parameters
    ----------
    start_x: Any
       The upper bound of the x-axis.
    end_x: Any
       The lower bound of the x-axis.
    upper_y: Anny
       The upper bound of the y-axis.
    lower_y: Anny
       The lower bound of the y-axis.
    """

    # Static lock used by all charts to ensure more than one chart isn't being plotted at the same time.
    plot_lock = threading.Lock()

    def __init__(self, start_x: Any = None, end_x: Any = None, upper_y: Any = None, lower_y: Any = None):
        # Matplotlib-specific fields.
        self._ax = None
        self._secondary_axes = None
        self.figure = None

        # Holds a mapping between decorator key and `Decorator`.
        self._decorators = OrderedDict()

        # Chart settings.
        self._start_x = start_x
        self._end_x = end_x
        self._upper_y = upper_y
        self._lower_y = lower_y

        ##############################################################################
        # Chart appearance settings, that cannot be set in the .mplstyle file. #
        ##############################################################################
        self.tick_fontweight = "normal"
        """
        x and y ticks' labels' font weight. Acceptable values:
        For more info, see: http://matplotlib.org/api/text_api.html#matplotlib.text.Text
        Acceptable values:
        [a numeric value in range 0-1000 | ‘ultralight’ | ‘light’ | ‘normal’ | ‘regular’ | ‘book’ | ‘medium’ |
        ‘roman’ |‘semibold’ | ‘demibold’ | ‘demi’ | ‘bold’ | ‘heavy’ | ‘extra bold’ | ‘black’ ]
        """

        self.tick_fontsize = None
        """
        x and y ticks' labels' font size. Acceptable values:
        [size in points | ‘xx-small’ | ‘x-small’ | ‘small’ | ‘medium’ | ‘large’ | ‘x-large’ | ‘xx-large’ ]
        """

        self.tick_color = None
        """
        Foreground color of all x and y ticks' labels. Acceptable values:
        Any matplotlib color, for example "black" or "#8ac72e".
        """

        self._orientation = Orientation.Vertical
        """
        Determines where secondary axes should be created. When Vertical, a vertical axes is created using ``twinx``,
        otherwise a horizontal axes is created using ``twiny``.
        """

    @property
    def axes(self):
        """
        Axes is the object on which the chart is plotted ("the drawing area").
        """
        return self._ax

    @axes.setter
    def axes(self, ax):
        self._ax = ax
        self.figure = ax.figure

    @property
    def secondary_axes(self):
        """
        A secondary axes on which data is plotted. Created by calling setup_secondary_axes_if_necessary.
        """
        return self._secondary_axes

    def plot(self, figsize: Tuple[float, float] = None):
        """
        Plots the chart. The underlying figure stays hidden until the show() method is called.

        Parameters
        ----------
        figsize: Tuple[float, float]
            The figure size to draw the chart at in inches. This is a tuple of (width, height) passed directly
            to matplotlib's ``plot`` function. The values are expressed in inches.
        """
        raise NotImplementedError

    def render_as_base64_image(
            self, figsize: Tuple[float, float] = None, dpi: int = 250, optimise: bool = False) -> str:
        """
        Plots the chart and returns the base64 image.
        """
        # Lock the plot_lock.
        with Chart.plot_lock:
            # Render the chart.
            self.plot(figsize)

            # Render as PNG.
            buffer = io.BytesIO()
            self.figure.savefig(buffer, format="PNG", dpi=dpi)

            buffer.seek(0)

        # Optimise file size.
        if optimise:
            img = Image.open(buffer)
            # Optimise image by changing its color space. Use the Antialias filter to preserve quality as much as
            # possible.
            img = img.convert("RGB").convert("P", palette=Image.ANTIALIAS)
            buffer.seek(0)
            # Re-save the image with the converted color space and with the optimise flag set to ensure PIL performs
            # an optimise pass on the file.
            img.save(buffer, format="PNG", optimize=True, quality=70)
            buffer.seek(0)

        # Encode as base64.
        return urllib.parse.quote(base64.b64encode(buffer.read()))

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        """
        Plots all DataElementDecorators added to a chart. This function should set `legend_artist` field in each
        plotted DataElementDecorator (if applicable).

        Parameters
        ----------
        data_element_decorators: List[DataElementDecorator]
            non-empty list of DataElementDecorators that should be plotted on the chart
        """
        raise NotImplementedError

    def show(self):
        """
        Shows the chart. It is necessary to call the plot function first.
        """
        self.figure.show()

    def close(self):
        """
        Closes the window containing the figure.
        """
        plt.close(self.figure)

    def set_x_range(self, start_x=None, end_x=None):
        self._start_x = start_x
        self._end_x = end_x

    def get_decorator(self, key: str):
        return self._decorators.get(key, None)

    @classmethod
    def assert_is_qfseries(cls, data_container: Any):
        from qf_lib.containers.series.qf_series import QFSeries
        if not isinstance(data_container, QFSeries):
            raise ValueError("Chart can only work with instances of QFSeries. "
                             "{} is not accepted as the data container".format(str(type(data_container))))

    @classmethod
    def determine_end_x(cls, start: datetime.datetime, series_list: List[Union[QFSeries, DataElementDecorator]]) \
            -> datetime.datetime:
        """
        Implements a heuristic for determining the x-axis end date based on a start date and series list.

        This is done by checking the year difference between the most recent date among the data points in all of the
        specified series and the specified start date. If the
        difference is greater than or equal to 10 years, the nearest date aligned to a 5 year boundary will be
        returned. Otherwise a datetime representing the nearest future January is returned.
        """
        assert len(series_list) > 0

        # Determine the most recent date out of all the data points in the specified series.
        latest_end_date = datetime.datetime(1, 1, 1)
        for data in series_list:
            # Presumably the last index will always be the most recent.
            series = data if isinstance(data, QFSeries) else data.data
            last_series_date = series.index[len(series) - 1]
            if last_series_date is not None and last_series_date > latest_end_date:
                latest_end_date = last_series_date

        # Determine (roughly) how many years passed since ``start``.
        years = (latest_end_date - start).days // 365

        the_year = latest_end_date.year
        if years >= 11:
            # Work out the nearest future year that is divisible by `the_range`.
            the_range = 5 if years >= 20 else 2
            for i in range(1, the_range + 1):
                if (the_year + i) % the_range == 0:
                    return datetime.datetime(the_year + i, 1, 1)
        else:
            return datetime.datetime(the_year + 1, 1, 1)

    @classmethod
    def get_axes_colors(cls) -> List[str]:
        """
        Returns the list of colors used for plotting on each Axes object. Colors are taken from the currently set
        plotting style.
        """
        return mpl.rcParams['axes.prop_cycle'].by_key()['color']

    def add_decorator(self, decorator: ChartDecorator) -> None:
        """
        Adds the new decorator to the chart.

        Each decorator must have a unique key that also doesn't clash with
        any series keys because both are used for legend label data. If there is already a decorator
        registered under the specified key, the operation will raise the AssertionError.

        Parameters
        ------------
        decorator: ChartDecorator
            decorator to be added
        """
        key = decorator.key
        assert key not in self._decorators, "The key '{}' is already used for another decorator.".format(key)

        self._decorators[key] = decorator

    def setup_secondary_axes_if_necessary(self):
        """
        Creates a secondary axes if one has not already been created.
        """
        if self._secondary_axes is None:
            self._setup_axes_if_necessary()
            self._secondary_axes = self.axes.twinx() if self._orientation == Orientation.Vertical else self.axes.twiny()

    def get_data_element_decorators(self):
        from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
        data_element_decorators = []

        for decorator in self._decorators.values():
            if isinstance(decorator, DataElementDecorator):
                data_element_decorators.append(decorator)
        return data_element_decorators

    def extract_series_data(self):
        """
        Extract data from data element decorators added to the chart.
        """
        result = []
        series = self.get_data_element_decorators()
        for i in range(0, len(series)):
            result.append(series[i].data.to_json())
        return result

    def _setup_axes_if_necessary(self, figsize: Tuple[float, float] = None):
        if self._ax is None:
            figure = plt.figure(figsize=figsize)
            ax = figure.add_subplot(1, 1, 1)  # (nrows, ncols, axnum)
            self.axes = ax
            # Set tick properties.
            for tick in self.axes.xaxis.get_major_ticks() + self.axes.yaxis.get_major_ticks():
                if self.tick_fontweight is not None:
                    tick.label1.set_fontweight(self.tick_fontweight)
                if self.tick_fontsize is not None:
                    tick.label1.set_fontsize(self.tick_fontsize)
                if self.tick_color is not None:
                    tick.label1.set_color(self.tick_color)
        if figsize is not None:
            # Make sure the specified figsize is set.
            self.axes.figure.set_size_inches(figsize[0], figsize[1])

    def _adjust_style(self):
        """
        Set's default style properties, which couldn't be set using style sheets.
        """
        # make x labels horizontal
        artist.setp(self.axes.xaxis.get_majorticklabels(), rotation=0, horizontalalignment='center')

        # Remove right and top lines around the graph.
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['top'].set_visible(False)

        # Only show ticks on left and bottom spines.
        self.axes.yaxis.set_ticks_position('left')
        self.axes.xaxis.set_ticks_position('bottom')

        # Move grid lines below all other lines.
        self.axes.set_axisbelow(True)

        # Set y-axis limits.
        if self._upper_y is not None or self._lower_y is not None:
            # Find the max value from all data series in the chart.
            max_value = self._get_data_max_value()
            if max_value is not None:
                # add 20% to give a bit of padding.
                max_value += max_value * 0.20
            # Find the min value from all data series in the chart.
            min_value = self._get_data_min_value()
            if min_value is not None:
                # subtract 20% to give a bit of padding.
                min_value -= min_value * 0.20

            # Use either the user-specified value or one that was computed above.
            top = max_value if self._upper_y is None else self._upper_y
            bottom = min_value if self._lower_y is None else self._lower_y
            assert top is not None, "Top must not be None. Is your chart missing series?"
            assert bottom is not None, "Bottom must not be None. Is your chart missing series?"
            self.axes.set_ylim(top=top, bottom=bottom)

    def _apply_decorators(self) -> None:
        from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
        from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator

        legend_decorators = []
        regular_decorators = []
        data_element_decorators = []

        # this method of assuring that LegendDecorator.decorate() is being called at the end is not the best way
        # to do it. It introduces a dependency of Chart on the LegendDecorator.
        for decorator in self._decorators.values():
            if isinstance(decorator, LegendDecorator):
                legend_decorators.append(decorator)
            elif isinstance(decorator, DataElementDecorator):
                data_element_decorators.append(decorator)
            else:
                regular_decorators.append(decorator)

        if data_element_decorators:
            self.apply_data_element_decorators(data_element_decorators)

        for decorator in regular_decorators + legend_decorators:
            decorator.decorate(self)

        # Set x-axis limits. These have to be set after decorators are applied.
        self.axes.set_xlim(self._start_x, self._end_x)

        if self._secondary_axes is not None:
            self._align_gridlines()

    def _align_gridlines(self):
        ax = self._ax
        ax2 = self._secondary_axes

        y1_min, y1_max = ax.get_ylim()
        y2_min, y2_max = ax2.get_ylim()

        y1_range = y1_max - y1_min
        y2_range = y2_max - y2_min

        y_ticks = ax.get_yticks()

        new_y2_ticks = y2_min + (y_ticks - y1_min) / y1_range * y2_range

        ax2.yaxis.set_major_locator(FixedLocator(new_y2_ticks))

    def _trim_data(self, data):
        if self._start_x is not None:
            data = data[data.index >= self._start_x]
        if self._end_x is not None:
            data = data[data.index <= self._end_x]

        return data

    def _generate_key(self, key: str = None) -> str:
        """
        Generates a new key if ``key`` is ``None``, otherwise returns ``key``.

        Used by LineChart and KDEChart.
        """
        adjusted_key = key
        if adjusted_key is None:
            adjusted_key = str(uuid.uuid4())

        assert adjusted_key not in self._decorators, "Key '{}' is already used.".format(adjusted_key)
        return adjusted_key

    def _get_data_min_value(self):
        result = None
        for key, decorator in self._decorators.items():
            if isinstance(decorator, DataElementDecorator):
                data_min = self._trim_data(decorator.data).dropna().values.min()
                if result is None or data_min < result:
                    result = data_min
        return result

    def _get_data_max_value(self):
        result = None
        for key, decorator in self._decorators.items():
            if isinstance(decorator, DataElementDecorator):
                data_max = self._trim_data(decorator.data).dropna().values.max()
                if result is None or data_max > result:
                    result = data_max
        return result
