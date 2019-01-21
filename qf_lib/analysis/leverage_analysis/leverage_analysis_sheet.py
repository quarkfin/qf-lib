from datetime import datetime
from os import path
from os.path import join

import matplotlib as plt

from qf_lib.common.utils.document_exporting import Document, ParagraphElement, ChartElement
from qf_lib.common.utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class LeverageAnalysisSheet(object):
    """
    Creates a PDF containing main statistics of the trades
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, leverage: QFSeries, title: str = "Leverage"):
        """
        leverage_tms
            list of Portfolio leverage values corresponding to the backtest trading conditions
        title
            title of the document, will be a part of the filename. Do not use special characters
        """
        self.leverage = leverage
        self.title = title

        self.document = Document(title)

        # position is linked to the position of axis in tearsheet.mplstyle
        self.full_image_size = (8, 2.4)
        self.full_image_axis_position = (0.08, 0.1, 0.892, 0.80)
        self.dpi = 400

        self.settings = settings
        self.pdf_exporter = pdf_exporter

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))
        self._add_leverage_chart()

    def _add_header(self):
        logo_path = join(get_starting_dir_abs_path(), self.settings.logo_path)
        company_name = self.settings.company_name
        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _add_leverage_chart(self):
        lev_chart = self._get_lev_chart()
        self.document.add_element(ChartElement(lev_chart, figsize=self.full_image_size, dpi=self.dpi))

    def _get_lev_chart(self):
        chart = LineChart()

        series_elem = DataElementDecorator(self.leverage)
        chart.add_decorator(series_elem)

        left, bottom, width, height = self.full_image_axis_position
        position_decorator = AxesPositionDecorator(left, bottom, width, height)
        chart.add_decorator(position_decorator)

        title_decorator = TitleDecorator("Leverage over time", key="title")
        chart.add_decorator(title_decorator)
        return chart

    def save(self, report_dir: str = ""):
        output_sub_dir = path.join(report_dir, "leverage_analysis")

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], output_sub_dir, filename)
