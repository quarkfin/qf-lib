from abc import ABCMeta
from datetime import datetime
from os import path
from typing import List

import matplotlib as plt

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.cone_chart import ConeChart
from qf_lib.plotting.charts.returns_heatmap_chart import ReturnsHeatmapChart
from qf_lib.plotting.helpers.create_return_quantiles import create_return_quantiles
from qf_lib.plotting.helpers.create_returns_bar_chart import create_returns_bar_chart
from qf_lib.plotting.helpers.create_skewness_chart import create_skewness_chart
from qf_lib.settings import Settings


class AbstractTearsheet(AbstractDocument, metaclass=ABCMeta):
    """
    Creates a PDF 'one-pager' as often found in institutional strategy performance reports.
    Includes an equity curve, drawdown curve, monthly returns, heatmap, yearly returns summary and other statistics

    Can be used with or without the benchmark
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, strategy_series: QFSeries,
                 live_date: datetime = None,
                 title: str = "Strategy Analysis"):
        super().__init__(settings, pdf_exporter, title)
        self.strategy_series = strategy_series
        self.live_date = live_date
        self.frequency = Frequency.DAILY

    def _add_perf_chart(self, series_list: List[QFSeries]):
        """
        series_list
            List of compared series. The strategy should always be the first element in the list
        """
        self.document.add_element(ChartElement(self._get_large_perf_chart(series_list),
                                               figsize=self.full_image_size, dpi=self.dpi))

    def _add_returns_statistics_charts(self):
        grid = self._get_new_grid()

        # Monthly returns heatmap
        heatmap_chart = ReturnsHeatmapChart(self.strategy_series)
        grid.add_chart(heatmap_chart)

        # Annual returns bar chart
        annual_ret_chart = create_returns_bar_chart(self.strategy_series)
        grid.add_chart(annual_ret_chart)
        self.document.add_element(grid)

    def _add_cone_and_quantiles(self):
        grid = self._get_new_grid()
        # Cone chart
        if self.live_date is not None:
            # use live_date to generate the cone chart (show only the OOS part in the cone)
            is_end_date = self.live_date
            nr_of_data_points = len(self.strategy_series.loc[self.live_date:])
        else:
            # use the 1Y of data or half of the series depending of what is shorter
            nr_of_data_points = min([self.frequency.value, round(len(self.strategy_series) / 2)])
            is_end_date = self.strategy_series.index[-nr_of_data_points]

        cone_chart = ConeChart(data=self.strategy_series, nr_of_data_points=nr_of_data_points, is_end_date=is_end_date)
        grid.add_chart(cone_chart)

        # Returns quantiles
        chart = create_return_quantiles(self.strategy_series, self.live_date)
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_underwater_and_skewness(self):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

        # Underwater plot
        grid.add_chart(self._get_underwater_chart(self.strategy_series))

        # Skewness chart
        chart = create_skewness_chart(self.strategy_series, title="Skewness")
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_statistics_table(self, series_list: List[QFSeries]):
        ta_list = [TimeseriesAnalysis(series, self.frequency) for series in series_list]
        super()._add_statistics_table(ta_list)

    def save(self, report_dir: str = ""):
        output_sub_dir = path.join(report_dir, "tearsheet")

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], output_sub_dir, filename)
