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

from typing import Tuple, List

import matplotlib as mpl
from pandas import date_range

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart


class CandlestickChart(Chart):
    """
    Plots a Candlestick chart for a prices data frame. The data frame should contain at least the following columns:
    - PriceField.Open
    - PriceField.Close
    - PriceField.High
    - PriceField.Low
    """
    def __init__(self, data: PricesDataFrame, title: str):
        super().__init__()

        assert all(price_field in data.columns for price_field
                   in [PriceField.Open, PriceField.Close, PriceField.High, PriceField.Low]), \
            "In order to plot the Candlestick Chart the data frame requires open, high, low and close prices"
        self.data = data
        self.title = title
        self.label_size = 5

        mpl.rc('ytick', labelsize=self.label_size)
        self.color_green = '#3CB371'
        self.color_red = '#FA8072'

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)
        ax = self.axes
        full_data = self.get_full_data_range(self.data)
        data_len = len(full_data)
        self.axes.set_xlim(0, data_len)

        if data_len > 1500:
            # plot line chart instead as there are too many bars
            data = PricesSeries(full_data.reset_index(drop=True)[PriceField.Close])
            self.axes.plot(data, linewidth=0.5)
        else:
            for index, data in enumerate(full_data.iterrows()):
                _, price_values = data
                self._plot_candlestick(price_values, index)

        # Format the x axis to show up to 10 x tick labels
        every_nth_tick = data_len // 10
        ax.set_xticks(range(0, data_len, every_nth_tick))
        ticks_to_be_plotted = full_data.index[::every_nth_tick]

        ax.tick_params(axis='both', which='major', labelsize=self.label_size)
        time_len = full_data.index[-1] - full_data.index[0]
        if time_len.days > 10:
            ticks_to_be_plotted = ticks_to_be_plotted.strftime('%Y-%m-%d')
            ax.set_xticklabels(ticks_to_be_plotted)
        else:
            ax.set_xticklabels(ticks_to_be_plotted, rotation=7)

        # Format the y axis
        formatter = mpl.ticker.FormatStrFormatter('%.2f')
        ax.yaxis.set_major_formatter(formatter)

        ax.set_title(self.title)

        self._apply_decorators()

    def get_full_data_range(self, container):
        full_range = date_range(self.data.index[0], self.data.index[-1],
                                freq=self.data.get_frequency()[PriceField.Close].to_pandas_freq())
        full_data = container.reindex(full_range)
        return full_data

    def add_highlight(self, highlight_series: QFSeries):
        """
        Add a background highlight to the plot. The highlights are based on the values in the highlight_series.

        Parameters
        ------------
        highlight_series: QFSeries
            Series containing values used to highlight the background. In case of values > 0 the background colour
            is set to green and in case of values < 0 the background colour is set to red. For all indices for which
            the values are equal to 0 the original background color is preserved.
        """
        full_series = self.get_full_data_range(highlight_series)
        full_series = full_series.ffill()

        self._setup_axes_if_necessary()

        previous_value = 0
        start_index = 0
        margin = 0.5
        for index, current_value in enumerate(full_series):
            # add red of green highlights of exposures
            if previous_value != current_value:
                if previous_value == 1:
                    self.axes.axvspan(start_index - margin, index - margin, facecolor=self.color_green, alpha=0.3)
                elif previous_value == -1:
                    self.axes.axvspan(start_index - margin, index - margin, facecolor=self.color_red, alpha=0.3)
                start_index = index
            previous_value = current_value

        # plot last highlight at the end if needed
        if previous_value == 1:
            self.axes.axvspan(start_index - margin, len(full_series), facecolor=self.color_green, alpha=0.3)
        elif previous_value == -1:
            self.axes.axvspan(start_index - margin, len(full_series), facecolor=self.color_red, alpha=0.3)

    def _plot_candlestick(self, data, index):
        """ Create a green rectangle in case of a rising price or a red one in case of a falling price. """
        color = self.color_green if data[PriceField.Close] > data[PriceField.Open] else self.color_red

        self.axes.plot([index, index], [data[PriceField.Low], data[PriceField.High]],
                       linewidth=0.2, color='black', zorder=2)

        rectangle = mpl.patches.Rectangle((index - 0.35, data[PriceField.Open]), 0.7,
                                          (data[PriceField.Close] - data[PriceField.Open]),
                                          facecolor=color, edgecolor='black', linewidth=0.3, zorder=3)
        self.axes.add_patch(rectangle)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        pass
