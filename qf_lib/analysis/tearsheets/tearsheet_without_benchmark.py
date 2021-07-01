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

from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.analysis.tearsheets.abstract_tearsheet import AbstractTearsheet
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.plotting.charts.returns_heatmap_chart import ReturnsHeatmapChart
from qf_lib.plotting.helpers.create_qq_chart import create_qq_chart
from qf_lib.plotting.helpers.create_returns_bar_chart import create_returns_bar_chart
from qf_lib.plotting.helpers.create_returns_distribution import create_returns_distribution
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class TearsheetWithoutBenchmark(AbstractTearsheet):
    """
    Creates a PDF report without a benchamrk.

    Parameters
    ----------
    settings: Settings
        settings of the project
    pdf_exporter: PDFExporter
        tool that creates the pdf with the result
    strategy_series: QFSeries
        timeseries of the trading of the strategy
    live_date: datetime
        if set it is used to generate the cone chart
    title: str
        title of the document
    """
    def __init__(self, settings: Settings, pdf_exporter, strategy_series: QFSeries, live_date: datetime = None,
                 title: str = "Strategy Analysis"):
        super().__init__(settings, pdf_exporter, strategy_series, live_date, title)

    def build_document(self):
        series_list = [self.strategy_series]

        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        self._add_perf_chart(series_list)
        self.document.add_element(ParagraphElement("\n"))

        self._add_returns_statistics_charts(self.strategy_series)
        self._add_ret_distribution_and_qq()

        self.document.add_element(ParagraphElement("\n"))

        self._add_rolling_ret_and_vol_chart(self.strategy_series)

        # Next Page
        self.document.add_element(NewPageElement())
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        self._add_cone_and_quantiles()
        self._add_underwater_and_skewness()

        self._add_statistics_table(series_list)

    def _add_ret_distribution_and_qq(self):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

        # Distribution of Monthly Returns
        chart = create_returns_distribution(self.strategy_series)
        grid.add_chart(chart)

        # QQ chart
        chart = create_qq_chart(self.strategy_series)
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_returns_statistics_charts(self, series):
        grid = self._get_new_grid()
        # Monthly returns heatmap
        heatmap_chart = ReturnsHeatmapChart(series, title="Monthly Returns - {}".format(series.name))
        grid.add_chart(heatmap_chart)

        # Annual returns bar chart
        annual_ret_chart = create_returns_bar_chart(series, title="Annual Returns - {}".format(series.name))
        grid.add_chart(annual_ret_chart)
        self.document.add_element(grid)
