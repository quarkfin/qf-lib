from datetime import datetime
from os import path

import matplotlib as plt

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.analysis.timeseries_analysis.timeseries_analysis_dto import TimeseriesAnalysisDTO
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.document_exporting import ParagraphElement
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.cone_chart_oos import ConeChartOOS
from qf_lib.settings import Settings


class LiveStrategySheet(AbstractDocument):
    """
    Contains set of statistics calculated for a strategy in live trading. Generates one page PDF with charts and tables
    """

    def __init__(self, settings: Settings, pdf_exporter,
                 strategy_series: QFSeries,
                 strategy_leverage: QFSeries,
                 is_tms_analysis: TimeseriesAnalysisDTO,
                 title: str = "Live Trading Sheet",
                 benchmark_series: QFSeries=None):

        super().__init__(settings, pdf_exporter, title)
        self.strategy_series = strategy_series
        self.strategy_leverage = strategy_leverage
        self.benchmark_series = benchmark_series
        self.is_tms_analysis = is_tms_analysis
        self.frequency = Frequency.DAILY

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        self._perf_and_cone()
        self.document.add_element(ParagraphElement("\n"))

        self._add_dd_and_leverage()
        self.document.add_element(ParagraphElement("\n"))

        ta_list = [TimeseriesAnalysis(self.strategy_series, self.frequency), self.is_tms_analysis]
        self._add_statistics_table(ta_list)

    def _perf_and_cone(self):
        grid = self._get_new_grid()

        perf_chart = self._get_perf_chart([self.strategy_series])
        grid.add_chart(perf_chart)

        cone_chart = ConeChartOOS(self.strategy_series,
                                  self.is_tms_analysis.daily_mean_ret, self.is_tms_analysis.daily_std)
        grid.add_chart(cone_chart)

        self.document.add_element(grid)

    def _add_dd_and_leverage(self):
        grid = self._get_new_grid()

        dd_chart = self._get_underwater_chart(self.strategy_series)
        grid.add_chart(dd_chart)

        leverage_chart = self._get_leverage_chart(self.strategy_leverage)
        grid.add_chart(leverage_chart)
        self.document.add_element(grid)

    def save(self, report_dir: str = ""):
        output_sub_dir = path.join(report_dir, "live_trading_sheet")

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], output_sub_dir, filename)
