from datetime import datetime
from os import path

import matplotlib as plt

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.settings import Settings


class LeverageAnalysisSheet(AbstractDocument):
    """
    Creates a PDF containing a visual representation of leverage changes over time
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, leverage: QFSeries, title: str = "Leverage"):
        """
        leverage_tms
            list of Portfolio leverage values corresponding to the backtest trading conditions
        title
            title of the document, will be a part of the filename. Do not use special characters
        """
        super().__init__(settings, pdf_exporter, title=title)
        self.leverage = leverage

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))
        self._add_leverage_chart()

    def _add_leverage_chart(self):
        lev_chart = self._get_leverage_chart(self.leverage)
        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        lev_chart.add_decorator(position_decorator)
        self.document.add_element(ChartElement(lev_chart, figsize=self.full_image_size, dpi=self.dpi))

    def save(self, report_dir: str = ""):
        output_sub_dir = path.join(report_dir, "leverage_analysis")

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], output_sub_dir, filename)
