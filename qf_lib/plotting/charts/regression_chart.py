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

from typing import Tuple

import matplotlib as mpl
import numpy as np
import pandas as pd

from qf_lib.common.utils.dateutils.get_values_common_dates import get_values_for_common_dates
from qf_lib.common.utils.returns.beta_and_alpha import beta_and_alpha_full_stats
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.axes_formatter_decorator import PercentageFormatter


class RegressionChart(Chart):
    """
    Creates a regression chart.

    Parameters
    -----------
    benchmark_tms: QFSeries
        timeseries of the benchmark
    strategy_tms: QFSeries
        timeseries of the strategy
    tail_plot: bool
        plot tail data
    custom_title: bool
        add custom title to the plot
    """
    def __init__(self, benchmark_tms: QFSeries, strategy_tms: QFSeries, tail_plot=False, custom_title=False):
        super().__init__()
        self.assert_is_qfseries(benchmark_tms)
        self.assert_is_qfseries(strategy_tms)

        self.benchmark_tms = benchmark_tms.to_simple_returns()
        self.strategy_tms = strategy_tms.to_simple_returns()
        self.tail_plot = tail_plot
        self.custom_title = custom_title

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)
        self._apply_decorators()

        datapoints_tms, regression_line, beta, alpha, r_squared, max_ret = self._prepare_data_to_plot()
        self._plot_data(datapoints_tms, regression_line, beta, alpha, r_squared, max_ret)

        if self.tail_plot:
            _, regression_line, beta, alpha, r_squared, max_ret = self._prepare_data_to_plot(tail=True)
            self._plot_tail_data(regression_line, beta, alpha, r_squared, max_ret)

        self.axes.set_xlabel(self.benchmark_tms.name)
        self.axes.set_ylabel(self.strategy_tms.name)
        if self.custom_title is not False and isinstance(self.custom_title, str):
            self.axes.set_title(self.custom_title)
        else:
            self.axes.set_title('Linear Regression')

    def _prepare_data_to_plot(self, tail=False):
        strategy_rets = self.strategy_tms.to_simple_returns()
        benchmark_rets = self.benchmark_tms.to_simple_returns()

        strategy_rets, benchmark_rets = get_values_for_common_dates(strategy_rets, benchmark_rets)
        datapoints_tms = pd.concat((benchmark_rets, strategy_rets), axis=1)

        if tail:
            def get_tail_indices():
                avg_rets = strategy_rets.mean()
                std_rets = strategy_rets.std()
                # Tail events are < the avg portfolio returns minus one std
                return strategy_rets < avg_rets - std_rets

            tail_indices = get_tail_indices()
            strategy_tail_returns = strategy_rets.loc[tail_indices]

            beta, alpha, r_value, p_value, std_err = beta_and_alpha_full_stats(
                strategy_tms=strategy_tail_returns, benchmark_tms=benchmark_rets)
        else:
            beta, alpha, r_value, p_value, std_err = beta_and_alpha_full_stats(
                strategy_tms=strategy_rets, benchmark_tms=benchmark_rets)

        max_ret = datapoints_tms.abs().max().max()  # take max element from the whole data-frame
        x = np.linspace(-max_ret, max_ret, 20)
        y = beta * x + alpha
        regression_line = QFSeries(data=y, index=pd.Float64Index(x))

        return datapoints_tms, regression_line, beta, alpha, r_value ** 2, max_ret

    def _plot_data(self, datapoints_tms, regression_line, beta, alpha, r_squared, max_ret):
        colors = Chart.get_axes_colors()

        self.axes.scatter(x=datapoints_tms.iloc[:, 0], y=datapoints_tms.iloc[:, 1],
                          c=colors[0], alpha=0.6, edgecolors='black', linewidths=0.5)

        self.axes.axhline(0, color='black', axes=self.axes, linewidth=1)
        self.axes.axvline(0, color='black', axes=self.axes, linewidth=1)

        self.axes.plot(regression_line.index.values, regression_line.values, axes=self.axes, color=colors[1])

        self.axes.set_xlim([-max_ret, max_ret])
        self.axes.set_ylim([-max_ret, max_ret])

        props = dict(boxstyle='square', facecolor='white', alpha=0.5)
        textstr = '$\\beta={0:.2f}$\n$\\alpha={1:.2%}$$\%$\n$R^2={2:.2}$'.format(beta, alpha, r_squared)
        font_size = mpl.rcParams['legend.fontsize']

        self.axes.text(
            0.05, 0.95, textstr, transform=self.axes.transAxes, bbox=props, verticalalignment='top', fontsize=font_size)

        self.axes.xaxis.set_major_formatter(PercentageFormatter())
        self.axes.yaxis.set_major_formatter(PercentageFormatter())

    def _plot_tail_data(self, regression_line, beta, alpha, r_squared, max_ret):
        colors = Chart.get_axes_colors()

        self.axes.plot(regression_line.index.values, regression_line.values, axes=self.axes, color=colors[2])

        self.axes.set_xlim([-max_ret, max_ret])
        self.axes.set_ylim([-max_ret, max_ret])

        props = dict(boxstyle='square', facecolor=colors[2], alpha=0.5)
        textstr = 'tail $\\beta={0:.2f}$\ntail $\\alpha={1:.2%}$$\%$\ntail $R^2={2:.2}$'.format(beta, alpha, r_squared)
        font_size = mpl.rcParams['legend.fontsize']

        self.axes.text(
            0.80, 0.35, textstr, transform=self.axes.transAxes, bbox=props, verticalalignment='top', fontsize=font_size)
