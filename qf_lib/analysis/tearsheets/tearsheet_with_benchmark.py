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

import scipy.stats as stats
import pandas as pd

from qf_lib.analysis.rolling_analysis.rolling_analysis import RollingAnalysisFactory
from qf_lib.analysis.tearsheets.abstract_tearsheet import AbstractTearsheet
from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.charts.regression_chart import RegressionChart
from qf_lib.plotting.charts.returns_heatmap_chart import ReturnsHeatmapChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.plotting.helpers.create_returns_bar_chart import create_returns_bar_chart
from qf_lib.plotting.helpers.create_returns_distribution import create_returns_distribution
from qf_lib.plotting.helpers.create_skewness_chart import create_skewness_chart
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class TearsheetWithBenchmark(AbstractTearsheet):
    """Creates a PDF report, which additionally contains a benchmark.

    Can be used with or without the benchmark

    Parameters
    ----------
    settings: Settings
        settings of the project
    pdf_exporter: PDFExporter
        tool that creates the pdf with the result
    strategy_series: QFSeries
        timeseries of the trading of the strategy
    benchmark_series: QFSeries
        timeseries of the benchmark
    live_date: datetime
        if set it is used to generate the cone chart
    title: str
        title of the document
    """
    def __init__(self, settings: Settings, pdf_exporter, strategy_series: QFSeries, benchmark_series: QFSeries,
                 live_date: datetime = None, title: str = "Strategy Analysis"):
        super().__init__(settings, pdf_exporter, strategy_series, live_date, title)
        self.benchmark_series = benchmark_series

    def build_document(self):
        series_list = [self.strategy_series, self.benchmark_series]

        # First Page
        self._add_header()
        self._add_perf_chart(series_list)
        self._add_relative_performance_chart(self.strategy_series, self.benchmark_series)
        self._add_statistics_table(series_list)

        # Second Page
        self.document.add_element(NewPageElement())
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        self._add_returns_statistics_charts()
        self._add_ret_distribution_and_similarity()
        self._add_rolling_table()

        # Third Page
        self.document.add_element(NewPageElement())
        self._add_header()

        self._add_cone_and_quantiles()
        self._add_underwater_and_skewness()

        self._add_rolling_return_chart(series_list)
        self.document.add_element(ParagraphElement("\n"))
        self._add_rolling_vol_chart(series_list)

        self.document.add_element(ParagraphElement("\n"))
        self._add_rolling_alpha_and_beta(series_list)

    def _add_returns_statistics_charts(self):
        grid = self._get_new_grid()
        # Monthly returns heatmap - Strategy
        heatmap_chart = ReturnsHeatmapChart(self.strategy_series, title="Monthly Returns - Strategy")
        grid.add_chart(heatmap_chart)

        # Annual returns bar chart - Strategy
        annual_ret_chart_strategy = create_returns_bar_chart(self.strategy_series, title="Annual Returns - Strategy")
        grid.add_chart(annual_ret_chart_strategy)

        # Monthly returns heatmap - Benchmark
        heatmap_chart = ReturnsHeatmapChart(self.benchmark_series, title="Monthly Returns - Benchmark")
        grid.add_chart(heatmap_chart)

        # Annual returns bar chart - Benchmark
        annual_ret_chart_benchmark = create_returns_bar_chart(self.benchmark_series, title="Annual Returns - Benchmark")
        grid.add_chart(annual_ret_chart_benchmark)
        self.document.add_element(grid)

        # put the same x axis range on both histograms
        min_x = min([annual_ret_chart_strategy.get_decorator("data_element").data.min(),
                     annual_ret_chart_benchmark.get_decorator("data_element").data.min(),
                     0])  # start at least form 0
        max_x = max([annual_ret_chart_strategy.get_decorator("data_element").data.max(),
                     annual_ret_chart_benchmark.get_decorator("data_element").data.max()])
        max_x = max_x + (max_x - min_x) / 8  # leave some space on the right to put the bar value

        annual_ret_chart_strategy.set_x_range(min_x, max_x)
        annual_ret_chart_benchmark.set_x_range(min_x, max_x)

    def _add_ret_distribution_and_similarity(self):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

        title = "Distribution of Monthly Returns - Strategy"
        chart_strategy = create_returns_distribution(self.strategy_series, title=title)
        grid.add_chart(chart_strategy)

        chart = RegressionChart(self.benchmark_series, self.strategy_series)
        grid.add_chart(chart)

        title = "Distribution of Monthly Returns - Benchmark"
        chart_benchmark = create_returns_distribution(self.benchmark_series, title=title)
        grid.add_chart(chart_benchmark)

        chart = RegressionChart(self.strategy_series, self.benchmark_series)
        grid.add_chart(chart)

        # put the same x axis range on both histograms
        min_x = min([chart_strategy.series.min(), chart_benchmark.series.min()])
        max_x = max([chart_strategy.series.max(), chart_benchmark.series.max()])
        chart_strategy.set_x_range(min_x, max_x)
        chart_benchmark.set_x_range(min_x, max_x)

        self.document.add_element(grid)

    def _add_underwater_and_skewness(self):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

        # Underwater plot
        grid.add_chart(self._get_underwater_chart(self.strategy_series, benchmark_series=self.benchmark_series))

        # Skewness chart
        chart = create_skewness_chart(self.strategy_series, title="Skewness")
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_rolling_table(self):
        dtos = RollingAnalysisFactory.calculate_analysis(self.strategy_series, self.benchmark_series)

        column_names = [
            Table.ColumnCell("Rolling Return Period", css_class="left-align"),
            "Strategy Average",
            "Strategy Worst",
            Table.ColumnCell("Strategy Best", css_class="right-align"),
            "Benchmark Average",
            "Benchmark Worst",
            Table.ColumnCell("Benchmark Best", css_class="right-align"),
            Table.ColumnCell("% Strategy outperform Benchmark", css_class="right-align")]
        result = Table(column_names, grid_proportion=GridProportion.Sixteen, css_class="table rolling-table")

        for dto in dtos:
            result.add_row([Table.Cell(dto.period, css_class="right-line"),
                            Table.Cell(dto.strategy_average, "{:.2%}"),
                            Table.Cell(dto.strategy_worst, "{:.2%}"),
                            Table.Cell(dto.strategy_best, "{:.2%}"),
                            Table.Cell(dto.benchmark_average, "{:.2%}"),
                            Table.Cell(dto.benchmark_worst, "{:.2%}"),
                            Table.Cell(dto.benchmark_best, "{:.2%}"),
                            Table.Cell(dto.percentage_difference, "{:.2%}")])

        self.document.add_element(result)

    def _add_rolling_alpha_and_beta(self, timeseries_list):
        freq = timeseries_list[0].get_frequency()
        timeseries_list = [tms.dropna().to_simple_returns() for tms in timeseries_list]
        df = pd.concat(timeseries_list, axis=1).fillna(0)

        rolling_window_len = int(freq.value / 2)  # 6M rolling
        step = round(freq.value / 6)  # 2M shift

        legend = LegendDecorator()
        chart = LineChart(start_x=df.index[0], end_x=df.index[-1])
        line_decorator = HorizontalLineDecorator(0, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)

        def alpha_function(df_in_window):
            strategy_returns = df_in_window.iloc[:, 0]
            benchmark_returns = df_in_window.iloc[:, 1]
            beta, alpha, _, _, _ = stats.linregress(benchmark_returns, strategy_returns)
            return beta, alpha

        rolling = df.rolling_time_window(rolling_window_len, step, alpha_function)
        rolling = pd.DataFrame([[b, a] for b, a in rolling.values], columns=["beta", "alpha"], index=rolling.index)

        rolling_element = DataElementDecorator(rolling["beta"])
        chart.add_decorator(rolling_element)
        legend.add_entry(rolling_element, "beta")

        rolling_element = DataElementDecorator(rolling["alpha"], use_secondary_axes=True)
        chart.add_decorator(rolling_element)
        legend.add_entry(rolling_element, "alpha")

        chart.add_decorator(legend)
        chart.add_decorator(AxesFormatterDecorator(use_secondary_axes=True, y_major=PercentageFormatter(".1f")))

        # modify axes position to make secondary scale visible
        axes_position = list(self.full_image_axis_position)
        axes_position[2] = axes_position[2] - 0.07
        position_decorator = AxesPositionDecorator(*axes_position)
        chart.add_decorator(position_decorator)

        title_str = "Rolling alpha and beta [{} {} samples]".format(rolling_window_len, freq)
        title_decorator = TitleDecorator(title_str, key="title")
        chart.add_decorator(title_decorator)
        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))
