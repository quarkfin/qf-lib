from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import List

import matplotlib as plt
from os.path import join

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.utils.document_exporting import Document, ChartElement, GridElement
from qf_lib.common.utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.common.utils.document_exporting.element.table import Table
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.get_sources_root import get_src_root
from qf_lib.plotting.charts.cone_chart import ConeChart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.charts.returns_heatmap_chart import ReturnsHeatmapChart
from qf_lib.plotting.charts.underwater_chart import UnderwaterChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.cone_decorator import ConeDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.plotting.decorators.top_drawdown_decorator import TopDrawdownDecorator
from qf_lib.plotting.helpers.create_return_quantiles import create_return_quantiles
from qf_lib.plotting.helpers.create_returns_bar_chart import create_returns_bar_chart
from qf_lib.plotting.helpers.create_skewness_chart import create_skewness_chart
from qf_lib.settings import Settings
from qf_lib.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis


class AbstractTearsheet(metaclass=ABCMeta):
    """
    Creates a PDF 'one-pager' as often
    found in institutional strategy performance reports.

    Includes an equity curve, drawdown curve, monthly returns, heatmap, yearly returns summary and other statistics

    Can be used with or without the benchmark
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, strategy_series: QFSeries,
                 live_date: datetime = None,
                 title: str = "Strategy Analysis"):
        self.strategy_series = strategy_series
        self.live_date = live_date
        self.title = title

        self.frequency = Frequency.DAILY
        self.document = Document(title)

        self.full_image_size = (8, 2.4)

        # position is linked to the position of axis in tearsheet.mplstyle
        self.full_image_axis_position = (0.08, 0.1, 0.892, 0.80)
        self.half_image_size = (4, 2.2)
        self.dpi = 400

        self.settings = settings
        self.pdf_exporter = pdf_exporter

    @abstractmethod
    def build_document(self):
        # main function that composes the document
        pass

    def _get_new_grid(self) -> GridElement:
        return GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

    def _add_header(self):
        logo_path = join(get_src_root(), self.settings.logo_path)
        company_name = self.settings.company_name

        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _add_perf_chart(self, series_list: List[QFSeries]):
        """
        series_list
            List of compared series. The strategy should always be the first element in the list
        """

        strategy = series_list[0].to_prices(1)
        chart = LineChart(start_x=strategy.index[0], end_x=strategy.index[-1])
        line_decorator = HorizontalLineDecorator(1, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)

        if self.live_date is not None:
            chart.add_decorator(ConeDecorator(strategy, self.live_date, cone_stds=1))

        legend = LegendDecorator()

        for series in series_list:
            strategy_tms = series.to_prices(1)
            series_elem = DataElementDecorator(strategy_tms)
            chart.add_decorator(series_elem)

            legend.add_entry(series_elem, strategy_tms.name)

        chart.add_decorator(legend)

        left, bottom, width, height = self.full_image_axis_position
        position_decorator = AxesPositionDecorator(left, bottom, width, height)
        chart.add_decorator(position_decorator)

        title_decorator = TitleDecorator("Strategy Performance", key="title")
        chart.add_decorator(title_decorator)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

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
            nr_of_data_points = min(
                [self.frequency.value, round(len(self.strategy_series) / 2)])
            is_end_date = self.strategy_series.index[-nr_of_data_points]

        cone_chart = ConeChart(
            data=self.strategy_series, nr_of_data_points=nr_of_data_points, is_end_date=is_end_date)
        grid.add_chart(cone_chart)

        # Returns quantiles
        chart = create_return_quantiles(self.strategy_series, self.live_date)
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_underwater_and_skewness(self):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

        # Underwater plot
        underwater_chart = UnderwaterChart(self.strategy_series, rotate_x_axis=True)
        underwater_chart.add_decorator(TopDrawdownDecorator(self.strategy_series, 5))
        underwater_chart.add_decorator(AxesLabelDecorator(y_label="Drawdown"))
        underwater_chart.add_decorator(TitleDecorator("Drawdown"))
        grid.add_chart(underwater_chart)

        # Skewness chart
        chart = create_skewness_chart(self.strategy_series, title="Skewness")
        grid.add_chart(chart)

        self.document.add_element(grid)

    def _add_statistics_table(self, series_list: List[QFSeries]):
        ta_list = [TimeseriesAnalysis(series, self.frequency) for series in series_list]

        table = Table(css_class="table stats-table")

        for ta in ta_list:
            ta.populate_table(table)
        self.document.add_element(table)

    def save(self):
        output_sub_dir = "tearsheet"

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], output_sub_dir, filename)
