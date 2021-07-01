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

from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.boxplot_chart import BoxplotChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_return_quantiles(returns: QFSeries, live_start_date: datetime = None, x_axis_labels_rotation: int = 20) \
        -> BoxplotChart:
    """
    Creates a new return quantiles boxplot chart based on the returns specified.

    A swarm plot is also rendered on the chart if the ``live_start_date`` is specified.

    Parameters
    ----------
    returns: QFSeries
        The returns series to plot on the chart.
    live_start_date: datetime
        The live start date that will determine whether a swarm plot should be rendered.
    x_axis_labels_rotation: int

    Returns
    -------
    BoxplotChart
        A new ``BoxplotChart`` instance.
    """

    simple_returns = returns.to_simple_returns()

    # case when we can plot IS together with OOS
    if live_start_date is not None:
        oos_returns = simple_returns.loc[simple_returns.index >= live_start_date]
        if len(oos_returns) > 0:
            in_sample_returns = simple_returns.loc[simple_returns.index < live_start_date]
            in_sample_weekly = get_aggregate_returns(in_sample_returns, Frequency.WEEKLY, multi_index=True)
            in_sample_monthly = get_aggregate_returns(in_sample_returns, Frequency.MONTHLY, multi_index=True)

            oos_weekly = get_aggregate_returns(oos_returns, Frequency.WEEKLY, multi_index=True)
            oos_monthly = get_aggregate_returns(oos_returns, Frequency.MONTHLY, multi_index=True)

            chart = BoxplotChart([in_sample_returns, oos_returns, in_sample_weekly,
                                  oos_weekly, in_sample_monthly, oos_monthly], linewidth=1)

            x_labels = ["daily IS", "daily OOS", "weekly IS", "weekly OOS", "monthly IS", "monthly OOS"]
            tick_decorator = AxisTickLabelsDecorator(labels=x_labels, axis=Axis.X, rotation=x_axis_labels_rotation)
        else:
            chart, tick_decorator = _get_simple_quantile_chart(simple_returns)

    else:  # case where there is only one set of data
        chart, tick_decorator = _get_simple_quantile_chart(simple_returns)

    chart.add_decorator(tick_decorator)

    # Set title.
    title = TitleDecorator("Return Quantiles")
    chart.add_decorator(title)
    chart.add_decorator(AxesLabelDecorator(y_label="Returns"))
    return chart


def _get_simple_quantile_chart(simple_returns):
    if len(simple_returns) > 0:
        simple_returns_weekly = get_aggregate_returns(simple_returns, Frequency.WEEKLY, multi_index=True)
        simple_returns_monthly = get_aggregate_returns(simple_returns, Frequency.MONTHLY, multi_index=True)

        chart = BoxplotChart([simple_returns, simple_returns_weekly, simple_returns_monthly], linewidth=1)
    else:
        chart = BoxplotChart([QFSeries(), QFSeries(), QFSeries()], linewidth=1)

    tick_decorator = AxisTickLabelsDecorator(labels=["daily", "weekly", "monthly"], axis=Axis.X)
    return chart, tick_decorator
