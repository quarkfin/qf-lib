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

from datetime import datetime
from typing import Iterable

import numpy as np

from qf_lib.common.enums.rebase_method import RebaseMethod
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_event_comparison_chart(
        series: QFSeries, event_dates_list: Iterable[datetime], title: str, samples_before: int = 100,
        samples_after: int = 200, rebase_method: RebaseMethod = RebaseMethod.divide) -> LineChart:
    """
    Creates a new chart based on a line chart. The chart puts all events at date = 0 and than compares the evolution
    of the series after the event date.

    Parameters
    ----------
    series: QFSeries
        Series usually with values of an index or level of interest rates
    event_dates_list: Iterable[datetime]
        A list specifying the dates of the events that we would like to compare. Each date will create
        a new series in the chart
    title: str
        The title of the graph, specify ``None`` if you don't want the chart to show a title.
    samples_before: int
        Number of samples shown on the chart that are before the event date
    samples_after: int
        Number of samples after the event date that are plotted on the chart
    rebase_method: RebaseMethod
        Specifies the way in which the data is normalised at the date of the event.

        - 'divide' - will divide all the values by the value at the date of the event
        - 'subtract' - will subtract the value at the event from the whole sample
        - 'none - will show the value as is (no rebasing).

    Returns
    -------
    LineChart
        The constructed ``LineChart``.
    """

    # Create a chart
    line_chart = LineChart()
    legend_decorator = LegendDecorator(key='legend')

    # For each date create a rebased series with event date index = 0
    for event_date in event_dates_list:
        # calculate the integer index of the beginning and end of the sample
        event_closest_date = series.index.asof(event_date)

        if isinstance(event_closest_date, datetime):
            event_date_int_index = series.index.get_indexer([event_closest_date])[0]
            start_index = event_date_int_index - samples_before
            end_index = event_date_int_index + samples_after
            end_index = min(end_index, series.count())

            # to simplify the algorithm accept only samples that are within the series
            if start_index >= 0 and end_index <= series.count():
                series_sample = series.iloc[start_index:end_index]
                value_at_event = series.asof(event_date)

                if rebase_method == RebaseMethod.divide:
                    series_sample = series_sample.div(value_at_event)
                elif rebase_method == RebaseMethod.subtract:
                    series_sample = series_sample.subtract(value_at_event)
                elif rebase_method == RebaseMethod.norebase:
                    series_sample = series_sample
                else:
                    raise ValueError("Incorrect rebase_method. Use 'divide', 'subtract' or 'norebase' ")

                new_index = np.array(range(0, series_sample.count())) - samples_before
                reindexed_series = QFSeries(data=series_sample.values, index=new_index)

                data_element = DataElementDecorator(reindexed_series)
                line_chart.add_decorator(data_element)

                legend_decorator.add_entry(data_element, event_date.strftime('%Y-%m-%d'))

    # Put vertical line at x = 0
    line_decorator = VerticalLineDecorator(x=0, key='vline', linestyle="dashed")
    line_chart.add_decorator(line_decorator)

    # Create a title
    title_decorator = TitleDecorator(title, key="title")
    line_chart.add_decorator(title_decorator)

    # Add a legend.
    line_chart.add_decorator(legend_decorator)

    return line_chart
