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

import warnings
from datetime import datetime
from typing import Tuple, Sequence, Any

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class SpanDecorator(ChartDecorator, SimpleLegendItem):
    """
    Uses a series of periods (tuples containing start date and end date of each period) to draw vertical spans
    (rectangles).

    Parameters
    ----------
    shadowed_periods: Sequence[Tuple[datetime, datetime]]
        sequence of tuples, where each tuple indicates a period that should be shadowed
        Example: [("2017-01-01", "2017-02-03"), ("2017-03-05", "2017-03-10")]
    key: str
        see ChartDecorator.key.__init__#key
    plot_settings
        additional plot settings for matplotlib
    """
    def __init__(self, shadowed_periods: Sequence[Tuple[datetime, datetime]], key: str = None, **plot_settings: Any):
        super().__init__(key)
        assert shadowed_periods  # check if list is not None and is not empty
        self._shadowed_periods = shadowed_periods
        self.plot_settings = plot_settings

    @classmethod
    def from_int_list(cls, series: QFSeries, key: str = None, **plot_settings: Any):
        warnings.warn("This method is deprecated. Use SpanDecorator.__init__() instead.")
        periods = cls._periods_from_int_series(series)
        return SpanDecorator(periods, key, **plot_settings)

    def decorate(self, chart: "Chart") -> None:
        axes = chart.axes

        self.plot_settings.setdefault('alpha', 0.3)
        self.plot_settings.setdefault('color', 'grey')

        for start_date, end_date in self._shadowed_periods:
            self.legend_artist = axes.axvspan(start_date, end_date, **self.plot_settings)

    @classmethod
    def _periods_from_int_series(cls, series: QFSeries) -> Sequence[Tuple[datetime, datetime]]:
        """
        Converts a time series with multiple 1/0 values into a condensed list of date ranges specifying where
        the rectangles should begin and end.

        For example:
            1920-03-31    0.0
            1920-06-30    1.0
            1920-09-30    1.0
            1920-12-31    0.0

        For this series, the area from 1920-06-30 to 1920-09-30 will be highlighted.
        """
        result = []  # List[Tuple[start_date, end_date]]

        start_date = None
        for index, value in series.iteritems():
            if value < 1.0 and start_date is not None:
                result.append((start_date, index))
                start_date = None
            if value >= 1.0 and start_date is None:
                start_date = index

        return result
