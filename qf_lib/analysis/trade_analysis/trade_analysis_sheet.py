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
from math import sqrt
from typing import Union, Tuple, Sequence, List, Callable, Optional

import matplotlib as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
from pandas import Timedelta

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.common.utils.returns.sqn import sqn, sqn_for100trades, avg_nr_of_trades_per1y
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.df_table import DFTable
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.histogram_chart import HistogramChart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_locator_decorator import AxesLocatorDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class TradeAnalysisSheet(AbstractDocument):
    """
    Creates a PDF containing main statistics of the trades.

    Parameters
    -------------
    settings: Settings
        settings of the project
    pdf_exporter: PDFExporter
        tool that creates the pdf with the result
    nr_of_assets_traded: int
        number of assets traded
    trades: Sequence[Trade]
        list of trades
    start_date: datetime
    end_date: datetime
    title: str
        title of the document, will be a part of the filename. Do not use special characters
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, nr_of_assets_traded: int, trades: Sequence[Trade],
                 start_date: datetime, end_date: datetime, initial_risk: Optional[float] = None, title: str = "Trades"):

        super().__init__(settings, pdf_exporter, title)

        self.start_date = start_date
        self.end_date = end_date
        self.initial_risk = initial_risk

        self.trades = sorted(trades, key=lambda t: (t.end_time, t.start_time))
        self.nr_of_assets_traded = nr_of_assets_traded

    def build_document(self):
        self._add_header()

        self._add_returns_distribution()
        self._add_stats_table()

        self._add_simulation_results()

    def _add_returns_distribution(self):
        if self.initial_risk is not None:
            returns = SimpleReturnsSeries(data=[t.percentage_pnl / self.initial_risk for t in self.trades])
            title = "Distribution of R multiples, Initial risk = {:.2%}".format(self.initial_risk)
            returns_histogram = self._get_distribution_plot(returns, title)
        else:
            returns = SimpleReturnsSeries(data=[t.percentage_pnl for t in self.trades])
            title = "Distribution of returns [%]"
            returns_histogram = self._get_distribution_plot(returns, title)

            # Format the x-axis so that its labels are shown as a percentage in case of percentage returns
            axes_formatter_decorator = AxesFormatterDecorator(x_major=PercentageFormatter(), key="axes_formatter")
            returns_histogram.add_decorator(axes_formatter_decorator)

        self.document.add_element(ChartElement(returns_histogram, figsize=self.full_image_size, dpi=self.dpi))

    def _add_stats_table(self):
        statistics = []  # type: List[Tuple]

        def append_to_statistics(measure_description: str, function: Callable, trades_containers,
                                 percentage_style: bool = False):
            style_format = "{:.2%}" if percentage_style else "{:.2f}"
            returned_values = (function(tc) for tc in trades_containers)
            returned_values = (value if is_finite_number(value) else 0.0 for value in returned_values)
            statistics.append((measure_description, *(style_format.format(val) for val in returned_values)))

        # Prepare trades data frame, used to generate all statistics
        trades_df = QFDataFrame.from_records(
            data=[(t.start_time, t.end_time, t.percentage_pnl, t.direction) for t in self.trades],
            columns=["start time", "end time", "percentage pnl", "direction"]
        )

        # In case if the initial risk is not set all the return statistic will be computed using the percentage pnl,
        # otherwise the r_multiply = percentage pnl / initial risk is used
        unit = "%" if self.initial_risk is None else "R"
        trades_df["returns"] = trades_df["percentage pnl"] if self.initial_risk is None \
            else trades_df["percentage pnl"] / self.initial_risk

        # Filter out only long and only
        long_trades_df = trades_df[trades_df["direction"] > 0]
        short_trades_df = trades_df[trades_df["direction"] < 0]
        all_dfs = [trades_df, long_trades_df, short_trades_df]

        append_to_statistics("Number of trades", len, all_dfs)
        append_to_statistics("% of trades number", lambda df: len(df) / len(trades_df) if len(trades_df) > 0 else 0,
                             all_dfs, percentage_style=True)

        period_length_in_years = Timedelta(self.end_date - self.start_date) / Timedelta(days=1) / DAYS_PER_YEAR_AVG
        append_to_statistics("Avg number of trades per year", lambda df: len(df) / period_length_in_years, all_dfs)
        append_to_statistics("Avg number of trades per year per asset",
                             lambda df: len(df) / period_length_in_years / self.nr_of_assets_traded, all_dfs)

        def percentage_of_positive_trades(df: QFDataFrame):
            return len(df[df["returns"] > 0]) / len(df) if len(df) > 0 else 0.0
        append_to_statistics("% of positive trades", percentage_of_positive_trades, all_dfs, percentage_style=True)

        def percentage_of_negative_trades(df: QFDataFrame):
            return len(df[df["returns"] < 0]) / len(df) if len(df) > 0 else 0.0
        append_to_statistics("% of negative trades", percentage_of_negative_trades, all_dfs, percentage_style=True)

        def avg_trade_duration(df: QFDataFrame):
            trades_duration = (df["end time"] - df["start time"]) / Timedelta(days=1)
            return trades_duration.mean()
        append_to_statistics("Average trade duration [days]", avg_trade_duration, all_dfs)

        append_to_statistics("Average trade return [{}]".format(unit), lambda df: df["returns"].mean(), all_dfs,
                             percentage_style=(self.initial_risk is None))
        append_to_statistics("Std trade return [{}]".format(unit), lambda df: df["returns"].std(), all_dfs,
                             percentage_style=(self.initial_risk is None))

        def avg_positive_trade_return(df: QFDataFrame):
            positive_trades = df[df["returns"] > 0]
            return positive_trades["returns"].mean()
        append_to_statistics("Average positive return [{}]".format(unit), avg_positive_trade_return, all_dfs,
                             percentage_style=(self.initial_risk is None))

        def avg_negative_trade_return(df: QFDataFrame):
            negative_trades = df[df["returns"] < 0]
            return negative_trades["returns"].mean()
        append_to_statistics("Average negative return [{}]".format(unit), avg_negative_trade_return, all_dfs,
                             percentage_style=(self.initial_risk is None))

        append_to_statistics("Best trade return [{}]".format(unit), lambda df: df["returns"].max(), all_dfs,
                             percentage_style=(self.initial_risk is None))
        append_to_statistics("Worst trade return [{}]".format(unit), lambda df: df["returns"].min(), all_dfs,
                             percentage_style=(self.initial_risk is None))

        append_to_statistics("SQN (per trade) [{}]".format(unit), lambda df: sqn(df["returns"]), all_dfs,
                             percentage_style=(self.initial_risk is None))
        append_to_statistics("SQN (per 100 trades) [{}]".format(unit), lambda df: sqn_for100trades(df["returns"]),
                             all_dfs, percentage_style=(self.initial_risk is None))

        def sqn_per_year(returns: QFSeries):
            sqn_per_year_value = sqn(returns) * sqrt(avg_nr_of_trades_per1y(returns, self.start_date, self.end_date))
            return sqn_per_year_value
        append_to_statistics("SQN (per year) [{}]".format(unit), lambda df: sqn_per_year(df["returns"]), all_dfs,
                             percentage_style=(self.initial_risk is None))

        statistics_df = QFDataFrame.from_records(statistics, columns=["Measure", "All trades", "Long trades",
                                                                      "Short trades"])
        table = DFTable(statistics_df, css_classes=['table', 'left-align'])
        table.add_columns_classes(["Measure"], 'wide-column')
        self.document.add_element(table)

    def _add_simulation_results(self):
        """
        Generate a data frame consisting of a certain number of "scenarios" (each scenario denotes one single equity
        curve).
        """
        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(level=1, text="Monte Carlo simulations\n"))
        self.document.add_element(HeadingElement(level=2, text="Average number of trades per year: {}\n".format(
            int(self._average_number_of_trades_per_year()))))
        if self.initial_risk is not None:
            self.document.add_element(HeadingElement(level=2, text="Initial risk: {:.2%}".format(self.initial_risk)))

        scenarios_df, total_returns = self._get_scenarios()

        # Plot all the possible paths on a chart
        all_paths_chart = self._get_simulation_plot(scenarios_df)
        self.document.add_element(ChartElement(all_paths_chart, figsize=self.full_image_size, dpi=self.dpi))

        # Plot the distribution plot
        distribution_plot = self._get_distribution_plot(
            total_returns, title="Monte Carlo Simulations Distribution (one year % return)", bins=200, crop=True)
        # Format the x-axis so that its labels are shown as a percentage in case of percentage returns

        axes_formatter_decorator = AxesFormatterDecorator(x_major=PercentageFormatter(), key="axes_formatter")
        distribution_plot.add_decorator(axes_formatter_decorator)

        self.document.add_element(ChartElement(distribution_plot, figsize=self.full_image_size, dpi=self.dpi))

        simulations_summary_table = self._get_monte_carlos_simulator_outputs(scenarios_df, total_returns)
        self.document.add_element(simulations_summary_table)

        # Extract the results of each of the scenarios and summarize the data in the tables
        dist_summary_tables = self._get_distribution_summary_table(total_returns)
        self.document.add_element(dist_summary_tables)

        # Add the "Chances of dropping below" and "Simulations summary" tables
        ruin_chances_table = self._get_chances_of_dropping_below_table(scenarios_df)
        self.document.add_element(ruin_chances_table)

    def _get_scenarios(self, num_of_scenarios: int = 2500) -> Tuple[PricesDataFrame, SimpleReturnsSeries]:
        # Generate scenarios, each of which consists of a certain number of trades, equal to the average number
        # of trades per year
        scenarios_generator = ScenariosGenerator()
        trade_returns = [trade.percentage_pnl for trade in self.trades]

        # Generate the scenarios
        scenarios_df = scenarios_generator.make_scenarios(
            trade_returns,
            scenarios_length=int(self._average_number_of_trades_per_year()),
            num_of_scenarios=num_of_scenarios
        )

        scenarios_df = scenarios_df.to_prices()

        return scenarios_df, scenarios_df.iloc[-1] / scenarios_df.iloc[0] - 1.0

    def _average_number_of_trades_per_year(self):
        """ Computes the average number of trades per year. """
        number_of_trades = len(self.trades)
        period_length_in_years = Timedelta(self.end_date - self.start_date) / Timedelta(days=1) / DAYS_PER_YEAR_AVG
        return number_of_trades / period_length_in_years

    def _get_simulation_plot(self, scenarios_df: PricesDataFrame) -> Chart:
        chart = LineChart(log_scale=True)

        for _, scenario in scenarios_df.items():
            data_element = DataElementDecorator(scenario, linewidth=0.5)
            chart.add_decorator(data_element)

        # Add a legend
        legend = LegendDecorator(key="legend_decorator")

        # Add Ensemble average
        ensemble_avg = scenarios_df.mean(axis=1)
        ensemble_avg_data_element = DataElementDecorator(ensemble_avg, color="#e1e5f4", linewidth=3)
        chart.add_decorator(ensemble_avg_data_element)
        legend.add_entry(ensemble_avg_data_element, "Ensemble average")

        # Add Expectation (vol adjusted)
        trade_returns = QFSeries(data=[trade.percentage_pnl for trade in self.trades])
        std = trade_returns.std()
        expectation_adj_series = np.ones(len(ensemble_avg)) * (trade_returns.mean() - 0.5 * std * std)
        expectation_adj_series = SimpleReturnsSeries(data=expectation_adj_series, index=ensemble_avg.index)
        expectation_adj_series = expectation_adj_series.to_prices()

        data_element = DataElementDecorator(expectation_adj_series, color="#46474b", linewidth=2)
        chart.add_decorator(data_element)
        legend.add_entry(data_element, "Expectation (vol adjusted)")

        # Add title
        title_decorator = TitleDecorator("Monte Carlo Simulations (log scale)", key="title")
        chart.add_decorator(title_decorator)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        chart.add_decorator(legend)

        return chart

    def _get_distribution_plot(self, data_series: SimpleReturnsSeries, title: str, bins: Union[int, str] = 50,
                               crop: bool = False):
        colors = Chart.get_axes_colors()

        if crop:
            start_x = np.quantile(data_series, 0.01)
            end_x = np.quantile(data_series, 0.99)
            chart = HistogramChart(data_series, bins=bins, start_x=start_x, end_x=end_x)
        else:
            chart = HistogramChart(data_series, bins=bins)

        # Only show whole numbers on the y-axis.
        y_axis_locator = MaxNLocator(integer=True)
        axes_locator_decorator = AxesLocatorDecorator(y_major=y_axis_locator, key="axes_locator")
        chart.add_decorator(axes_locator_decorator)

        # Add an average line.
        avg_line = VerticalLineDecorator(data_series.mean(), color=colors[1],
                                         key="average_line_decorator", linestyle="--", alpha=0.8)
        chart.add_decorator(avg_line)

        # Add a legend.
        legend = LegendDecorator(key="legend_decorator")
        legend.add_entry(avg_line, "Mean")
        chart.add_decorator(legend)

        # Add a title.
        title_decorator = TitleDecorator(title, key="title")
        chart.add_decorator(title_decorator)
        chart.add_decorator(AxesLabelDecorator(title, "Occurrences"))

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        return chart

    def _get_distribution_summary_table(self, scenarios_results: SimpleReturnsSeries) -> DFTable:
        rows = []
        percentage_list = [0.05, 0.1, 0.2, 0.3]
        for percentage in percentage_list:
            rows.append(("{:.0%} Tail".format(percentage),
                         "{:.2%}".format(np.quantile(scenarios_results, percentage))))

        rows.append(("50%", "{:.2%}".format(np.quantile(scenarios_results, 0.5))))

        for percentage in reversed(percentage_list):
            rows.append(("{:.0%} Top".format(percentage),
                         "{:.2%}".format(np.quantile(scenarios_results, (1.0 - percentage)))))

        table = DFTable(data=QFDataFrame.from_records(rows, columns=["Measure", "Value"]),
                        css_classes=['table', 'left-align'])
        table.add_columns_classes(["Measure"], 'wide-column')

        return table

    def _get_chances_of_dropping_below_table(self, scenarios_df: PricesDataFrame) -> DFTable:
        _, all_scenarios_number = scenarios_df.shape
        rows = []

        crop_table = False
        for percentage in np.linspace(0.1, 0.9, 9):
            # Count number of scenarios, whose returns at some point of time dropped below the percentage * initial
            # value
            _, scenarios_above_percentage = scenarios_df.where(scenarios_df > (1.0 - percentage)).dropna(axis=1).shape
            probability = (all_scenarios_number - scenarios_above_percentage) / all_scenarios_number

            rows.append(("{:.0%}".format(percentage), "{:.2%}".format(probability)))

            if crop_table is True:
                break
            elif probability < 0.1:
                crop_table = True

        table = DFTable(QFDataFrame.from_records(rows, columns=["Chances of dropping below", "Probability"]),
                        css_classes=['table', 'left-align'])
        table.add_columns_classes(["Chances of dropping below"], 'wide-column')
        return table

    def _get_monte_carlos_simulator_outputs(self, scenarios_df: PricesDataFrame, total_returns: SimpleReturnsSeries) \
            -> DFTable:
        _, all_scenarios_number = scenarios_df.shape
        rows = []

        # Add the Median Return value
        median_return = np.median(total_returns)
        rows.append(("Median Return", "{:.2%}".format(median_return)))

        # Add the Mean Return value
        mean_return = total_returns.mean()
        rows.append(("Mean Return", "{:.2%}".format(mean_return)))

        trade_returns = QFSeries(data=[trade.percentage_pnl for trade in self.trades])
        sample_len = int(self._average_number_of_trades_per_year())
        std = trade_returns.std()
        expectation_adj_series = np.ones(sample_len) * (trade_returns.mean() - 0.5 * std * std)
        expectation_adj_series = SimpleReturnsSeries(data=expectation_adj_series)
        expectation_adj_series = expectation_adj_series.to_prices(suggested_initial_date=0)
        mean_volatility_adjusted_return = expectation_adj_series.iloc[-1] / expectation_adj_series.iloc[0] - 1.0
        rows.append(("Mean Volatility Adjusted Return", "{:.2%}".format(mean_volatility_adjusted_return)))

        # Add the Median Drawdown
        max_drawdowns = max_drawdown(scenarios_df)
        median_drawdown = np.median(max_drawdowns)
        rows.append(("Median Maximum Drawdown", "{:.2%}".format(median_drawdown)))

        # Add the Median Return / Median Drawdown
        rows.append(("Return / Drawdown", "{:.2f}".format(median_return / median_drawdown)))

        # Probability, that the return will be > 0
        scenarios_with_positive_result = total_returns[total_returns > 0.0].count()
        probability = scenarios_with_positive_result / all_scenarios_number
        rows.append(("Probability of positive return", "{:.2%}".format(probability)))

        table = DFTable(data=QFDataFrame.from_records(rows, columns=["Measure", "Value"]),
                        css_classes=['table', 'left-align'])
        table.add_columns_classes(["Measure"], 'wide-column')

        return table

    def save(self, report_dir: str = "trades_analysis"):

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], report_dir, filename)
