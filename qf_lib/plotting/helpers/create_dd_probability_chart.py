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

from collections import Sequence
from typing import Tuple

import numpy as np

from qf_lib.common.utils.returns.list_of_max_drawdowns import list_of_max_drawdowns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.scatter_decorator import ScatterDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_dd_probability_chart(prices_tms: QFSeries, bear_market_definition: float = 0.2) -> Tuple[Chart, Chart]:
    """Creates drawdowns probability chart.

    Parameters
    ----------
    prices_tms: QFSeries
        timeseries of prices
    bear_market_definition: float
        definition of bear market threshold

    Returns
    -------
    Tuple[Chart, Chart]
        Returns two charts - one showing the probability of drawdowns going beyond a certain level and one showing the
        marginal increase of probability of drawdowns going beyond the given level.
    """

    def count_dd_above_threshold(drawdown_series: Sequence, threshold: float):
        return sum(1 for dd in drawdown_series if dd > threshold)

    drawdowns, duration_of_drawdowns = list_of_max_drawdowns(prices_tms)

    examined_dds = np.arange(0.01, bear_market_definition, 0.005)
    percentage_ending_in_bear_market = []
    nr_of_bear_markets = count_dd_above_threshold(drawdowns, bear_market_definition)

    for examined_dd in examined_dds:
        number_of_dds_above = count_dd_above_threshold(drawdowns, examined_dd)
        percentage = nr_of_bear_markets / number_of_dds_above * 100
        percentage_ending_in_bear_market.append(percentage)

    chart = LineChart()
    chart.add_decorator(ScatterDecorator(examined_dds * 100, percentage_ending_in_bear_market, edgecolors='black'))
    chart.add_decorator(TitleDecorator(
        "Percentage of drawdowns going beyond {:2.0f}%".format(bear_market_definition * 100)))
    axis_dec = AxesLabelDecorator(
        "examined drawdown [%]",
        "chance that drawdown will go beyond {:2.0f}% in [%]".format(bear_market_definition * 100))
    chart.add_decorator(axis_dec)
    x_axis_values = examined_dds * 100
    prob_of_dd_chart = LineChart()
    prob_of_dd_chart.add_decorator(ScatterDecorator(
        x_axis_values, percentage_ending_in_bear_market, edgecolors='black'))
    prob_of_dd_chart.add_decorator(TitleDecorator(
        "Percentage of drawdowns going beyond {:2.0f}%".format(bear_market_definition * 100)))
    axis_dec = AxesLabelDecorator(
        "examined drawdown [%]",
        "chance that drawdown will go beyond {:2.0f}% in [%]".format(bear_market_definition * 100))
    prob_of_dd_chart.add_decorator(axis_dec)

    marginal_increase_in_prob_chart = LineChart()
    diff = np.diff([0] + percentage_ending_in_bear_market)
    marginal_increase_in_prob_chart.add_decorator(ScatterDecorator(x_axis_values, diff, edgecolors='black'))
    marginal_increase_in_prob_chart.add_decorator(TitleDecorator(
        "Marginal increase of probability of drawdowns going beyond {:2.0f}%".format(bear_market_definition * 100)))
    axis_dec = AxesLabelDecorator(
        "examined drawdown [%]",
        "Marginal increase of chance that drawdown will go beyond {:2.0f}% in [%]".format(bear_market_definition * 100))
    marginal_increase_in_prob_chart.add_decorator(axis_dec)

    return prob_of_dd_chart, marginal_increase_in_prob_chart
