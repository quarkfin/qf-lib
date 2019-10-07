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

from qf_lib.analysis.rolling_analysis.rolling_analysis import RollingAnalysisFactory
from qf_lib.analysis.tearsheets.abstract_tearsheet import AbstractTearsheet
from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.plotting.charts.regression_chart import RegressionChart
from qf_lib.plotting.helpers.create_returns_distribution import create_returns_distribution
from qf_lib.settings import Settings


class TearsheetWithBenchmark(AbstractTearsheet):

    def __init__(self, settings: Settings, pdf_exporter, strategy_series: QFSeries, benchmark_series: QFSeries,
                 live_date: datetime = None, title: str = "Strategy Analysis"):
        super().__init__(settings, pdf_exporter, strategy_series, live_date, title)
        self.benchmark_series = benchmark_series

    def build_document(self):
        series_list = [self.strategy_series, self.benchmark_series]

        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        self._add_perf_chart(series_list)
        self.document.add_element(ParagraphElement("\n"))

        self._add_returns_statistics_charts()
        self.document.add_element(ParagraphElement("\n"))

        self._add_ret_distribution_and_similarity()
        self.document.add_element(ParagraphElement("\n"))

        self._add_rolling_table()

        # Next Page
        self.document.add_element(NewPageElement())
        self.document.add_element(ParagraphElement("\n"))

        self._add_cone_and_quantiles()
        self._add_underwater_and_skewness()

        self._add_statistics_table(series_list)

        # Next Page
        self.document.add_element(NewPageElement())

        self._add_header()

        self.document.add_element(ParagraphElement("\n"))
        self.document.add_element(ParagraphElement("\n"))

        self._add_rolling_chart(self.strategy_series)

        self.document.add_element(ParagraphElement("\n"))
        self.document.add_element(ParagraphElement("\n"))

        self._add_rolling_chart(self.benchmark_series)

    def _add_ret_distribution_and_similarity(self):
        grid = GridElement(mode=PlottingMode.PDF,
                           figsize=self.half_image_size, dpi=self.dpi)
        # Distribution of Monthly Returns
        chart = create_returns_distribution(self.strategy_series)
        grid.add_chart(chart)

        # Regression chart
        chart = RegressionChart(self.benchmark_series, self.strategy_series)
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_rolling_table(self):
        dtos = RollingAnalysisFactory.calculate_analysis(self.strategy_series, self.benchmark_series)

        column_names = [
            Table.ColumnCell("Rolling Return Period"),
            "Strategy Average",
            "Strategy Worst",
            Table.ColumnCell("Strategy Best"),
            "Benchmark Average",
            "Benchmark Worst",
            Table.ColumnCell("Benchmark Best"),
            Table.ColumnCell("% Strategy outperform Benchmark")]
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
