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

import matplotlib as plt

from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.analysis.tearsheets.abstract_tearsheet import AbstractTearsheet
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.plotting.charts.cone_chart_oos import ConeChartOOS
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class StrategyMonitoringDocument(AbstractTearsheet):
    """Creates PDF with strategy monitoring analysis.

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
    def __init__(self, settings: Settings, pdf_exporter, strategy_series: QFSeries, benchmark_series: QFSeries,
                 live_date: datetime = None, title: str = "Strategy Analysis"):
        super().__init__(settings, pdf_exporter, strategy_series, live_date, title)

        self.is_mean_return = None
        self.is_sigma = None

        self.excess_is_mean_return = None
        self.excess_is_sigma = None

        self.benchmark_series = benchmark_series

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n\n"))

        series_list = [self.strategy_series, self.benchmark_series]
        self._add_perf_chart(series_list)
        self.document.add_element(ParagraphElement("\n\n"))

        self._add_relative_performance_chart(self.strategy_series, self.benchmark_series)
        self.document.add_element(ParagraphElement("\n\n"))

        self._add_excess_cone_chart()
        self.document.add_element(ParagraphElement("\n\n"))

        self._add_rolling_return_chart(series_list)
        self.document.add_element(ParagraphElement("\n\n"))

        self._add_rolling_vol_chart(series_list)

    def set_in_sample_statistics(self, is_mean_return, is_sigma):
        self.is_mean_return = is_mean_return
        self.is_sigma = is_sigma

    def set_in_sample_excess_statistics(self, excess_is_mean_return, excess_is_sigma):
        self.excess_is_mean_return = excess_is_mean_return
        self.excess_is_sigma = excess_is_sigma

    def _add_excess_cone_chart(self):
        diff = self.strategy_series.to_simple_returns().subtract(self.benchmark_series.to_simple_returns(),
                                                                 fill_value=0)
        diff = diff.iloc[-200:]
        diff = diff.to_prices(1)
        cone_chart = ConeChartOOS(diff,
                                  is_mean_return=self.excess_is_mean_return,
                                  is_sigma=self.excess_is_sigma,
                                  title="Excess returns")

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        cone_chart.add_decorator(position_decorator)

        chart_element = ChartElement(cone_chart, self.full_image_size, self.dpi, False)
        self.document.add_element(chart_element)

    def save(self, report_dir: str = "", file_name=None):
        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], report_dir, filename)
