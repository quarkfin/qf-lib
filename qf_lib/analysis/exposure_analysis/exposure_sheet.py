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

from typing import Tuple
from matplotlib.cm import get_cmap
from matplotlib.dates import DateFormatter
from matplotlib.ticker import StrMethodFormatter
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.common.enums.matplotlib_location import AxisLocation
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator_custom_position import LegendDecoratorCustomPosition
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings
import matplotlib as plt
from datetime import datetime


@ErrorHandling.class_error_logging()
class ExposureSheet(AbstractDocument):
    """
    Creates an Exposure Sheet in PDF format

    Parameters
    ----------
    settings: Settings
        settings of the project
    pdf_exporter: PDFExporter
        tool that creates the pdf with the result
    title: str
        title of the document. Default: Exposure Sheet
    axis_position: Tuple[float, float, float, float]
        position of the axes (the area of the chart) on the figure
    """
    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, title: str = "Exposure Sheet",
                 axis_position: Tuple[float, float, float, float] = (0.1125, 0.1, 0.850, 0.80)):
        super().__init__(settings, pdf_exporter, title)
        self._sector_data = None
        self._factor_data = None
        self.axis_position = axis_position

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        if self._sector_data is not None:
            self._add_chart(self._sector_data, self._sector_data.name)

        if self._factor_data is not None:
            self._add_chart(self._factor_data, self._factor_data.name)

    def save(self, report_dir: str = ""):
        # Set the style for the report
        plt.style.use(['tearsheet'])
        filename = "%Y_%m_%d-%H%M {}.pdf".format("Exposure Sheet")
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], report_dir, filename)

    def set_sector_data(self, sector_data: QFDataFrame):
        """
        Sets coefficients of sector-related regressors

        Parameters
        ----------
        sector_data: QFDataFrame
            QFDataFrame that contains coefficients for sector-related regressors
        """
        self._sector_data = sector_data

    def set_factor_data(self, factor_data: QFDataFrame):
        """
        Sets coefficients of factor-related regressors

        Parameters
        ----------
        factor_data: QFDataFrame
            QFDataFrame that contains coefficients for factor-related regressors
        """
        self._factor_data = factor_data

    def _add_chart(self, df: QFDataFrame, title: str):
        chart = self._create_chart(df, title)
        self.document.add_element(
            ChartElement(
                chart=chart,
                figsize=self.full_image_size,
                dpi=self.dpi,
            )
        )

    def _create_chart(self, df: QFDataFrame, title: str):
        chart = LineChart()
        # Place legend on bottom right corner of plot
        legend = LegendDecoratorCustomPosition(legend_placement=AxisLocation.LOWER_LEFT)
        cmap = get_cmap("tab10", len(df.columns))

        # iterate columns
        for column, label, color_index in zip(df.columns, df.columns.values, range(0, cmap.N)):
            data = df.loc[:, column]
            data_value_decorator = DataElementDecorator(data, color=cmap(color_index))
            chart.add_decorator(data_value_decorator)
            legend.add_entry(data_value_decorator, label)

        chart.add_decorator(
            AxesFormatterDecorator(
                x_major=DateFormatter(fmt=str(DateFormat.YEAR_DOT_MONTH)),
                y_major=StrMethodFormatter("{x:.2f}"),
            )
        )

        chart.add_decorator(AxesPositionDecorator(*self.axis_position))
        chart.add_decorator(TitleDecorator(title))
        chart.add_decorator(legend)
        return chart
