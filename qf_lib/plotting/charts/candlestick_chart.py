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

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
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

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize)
        ax = self.axes

        for index, data in enumerate(self.data.iterrows()):
            _, price_values = data
            self._plot_candlestick(price_values, index)

        # Format the x axis to show up to 10 x tick labels
        every_nth_tick = len(self.data) // 10
        ax.set_xticks(range(0, len(self.data), every_nth_tick))
        ticks_to_be_plotted = self.data.index[::every_nth_tick]

        series_frequency, _ = self.data.infer_interval()
        # In case of daily timeseries do not show the hours and mintues part
        if series_frequency.days >= 1:
            ticks_to_be_plotted = ticks_to_be_plotted.strftime('%Y-%m-%d')

        ax.set_xticklabels(ticks_to_be_plotted, rotation=10, fontsize=6)

        # Format the y axis
        formatter = mpl.ticker.FormatStrFormatter('%.2f')
        ax.yaxis.set_major_formatter(formatter)

        ax.set_title(self.title)

        self._apply_decorators()

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
        reindexed_series = highlight_series.reindex(self.data.index)
        self._setup_axes_if_necessary()

        for indx, value in enumerate(reindexed_series):
            if value > 0:
                self.axes.axvspan(indx - 0.5, indx + 0.5, facecolor='#3CB371', alpha=0.4)
            elif value < 0:
                self.axes.axvspan(indx - 0.5, indx + 0.5, facecolor='#FA8072', alpha=0.4)

    def _plot_candlestick(self, data, index):
        """ Create a green rectangle in case of a rising price or a red one in case of a falling price. """
        color = "#3CB371" if data[PriceField.Close] > data[PriceField.Open] else "#FA8072"
        self.axes.plot([index, index], [data[PriceField.Low], data[PriceField.High]], linewidth=0.2, color='black', zorder=2)

        rectangle = mpl.patches.Rectangle((index - 0.35, data[PriceField.Open]), 0.7,
                                          (data[PriceField.Close] - data[PriceField.Open]),
                                          facecolor=color, edgecolor='black', linewidth=0.2, zorder=3)
        self.axes.add_patch(rectangle)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        pass
