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
from os import path

import matplotlib as plt

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.is_return_stats import InSampleReturnStats
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.cone_chart_oos import ConeChartOOS
from qf_lib.settings import Settings


class LiveTradingSheet(AbstractDocument):
    """
    Contains set of statistics calculated for a strategy in live trading. Generates one page PDF with charts and tables.

    Parameters
    ----------
    settings: Settings
        settings of the project
    pdf_exporter: PDFExporter
        tool that creates the pdf with the result
    strategy_tms: QFSeries
        timeseries of the live trading of the strategy
    strategy_leverage_tms: QFSeries
        timeseries of the leverage during the live trading period
    is_stats: InSampleReturnStats
        statistics of the In Sample period of the strategy
    title: str
        title of the document
    benchmark_tms: None, QFSeries
        timeseries of the benchmark corresponding to the strategy_tms
    """

    def __init__(self, settings: Settings, pdf_exporter,
                 strategy_tms: QFSeries,
                 strategy_leverage_tms: QFSeries,
                 is_stats: InSampleReturnStats,
                 title: str = "Live Trading Sheet",
                 benchmark_tms: QFSeries = None):

        super().__init__(settings, pdf_exporter, title)
        self.strategy_tms = strategy_tms
        self.benchmark_tms = benchmark_tms
        self._add_default_names_if_needed(strategy_tms)
        self.strategy_leverage_tms = strategy_leverage_tms
        self.is_stats = is_stats
        self.frequency = Frequency.DAILY

    def build_document(self):
        self._add_header()
        self._perf_and_cone()
        self._add_dd_and_leverage()

        if self.benchmark_tms is None:
            ta_list = [TimeseriesAnalysis(self.strategy_tms, self.frequency)]
        else:
            ta_list = [TimeseriesAnalysis(self.strategy_tms, self.frequency),
                       TimeseriesAnalysis(self.benchmark_tms, self.frequency)]
        self._add_statistics_table(ta_list)

    def _perf_and_cone(self):
        grid = self._get_new_grid()
        series_list = [self.strategy_tms] if self.benchmark_tms is None \
            else [self.strategy_tms, self.benchmark_tms]

        perf_chart = self._get_small_perf_chart(series_list)
        grid.add_chart(perf_chart)

        cone_chart = ConeChartOOS(self.strategy_tms,
                                  self.is_stats.mean_log_ret, self.is_stats.std_of_log_ret)
        grid.add_chart(cone_chart)
        self.document.add_element(grid)

    def _add_dd_and_leverage(self):
        grid = self._get_new_grid()

        dd_chart = self._get_underwater_chart(self.strategy_tms)
        grid.add_chart(dd_chart)

        leverage_chart = self._get_leverage_chart(self.strategy_leverage_tms, rotate_x_axis=True)
        grid.add_chart(leverage_chart)
        self.document.add_element(grid)

    def save(self, report_dir: str = ""):
        output_sub_dir = path.join(report_dir, "live_trading_sheet")

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], output_sub_dir, filename)

    def _add_default_names_if_needed(self, strategy_tms):
        if strategy_tms.name is None:
            self.strategy_tms.name = "Live Trading Performance"
        if self.benchmark_tms is not None and self.benchmark_tms.name is None:
            self.benchmark_tms.name = "Benchmark"
