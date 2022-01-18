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

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.documents_utils.document_exporting.element.df_table import DFTable
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class CurrentPositionsSheet(AbstractDocument):
    """ Provides information about currently open positions in the portfolio. Provides a list of tickers, position
    directions, total exposure value, profit and loss and time of the position creation.

    Parameters
    -----------
    settings: Settings
        necessary settings
    pdf_exporter: PDFExporter
        used to export the document to PDF
    portfolio: Portfolio
        portfolio containing all historical and current trading data
    title: str
        title of the document
    """
    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, portfolio: Portfolio,
                 title: str = "Current Positions"):
        super().__init__(settings, pdf_exporter, title)
        self._portfolio = portfolio

    def build_document(self):
        self._add_header()

        self.document.add_element(ParagraphElement("\n"))
        self.document.add_element(HeadingElement(level=2, text="Open Positions in the Portfolio"))
        self._add_open_positions_table()

    def _add_open_positions_table(self):
        open_positions_dict = self._portfolio.open_positions_dict
        tickers = open_positions_dict.keys()

        # Get the information whether it is a long or short position
        directions = [open_positions_dict[t].direction() for t in tickers]
        directions = ["LONG" if direction == 1 else "SHORT" for direction in directions]

        # Get the total exposure and market value for each open position
        total_exposures = ["{:,.2f}".format(open_positions_dict[t].total_exposure()) for t in tickers]
        pnls = ["{:,.2f}".format(open_positions_dict[t].unrealised_pnl) for t in tickers]

        # Get the time of opening the positions
        start_time = [open_positions_dict[t].start_time.date() for t in tickers]

        data = {
            "Tickers name": [t.name for t in tickers],
            "Specific ticker": tickers,
            "Direction": directions,
            "Total Exposure": total_exposures,
            "PnL": pnls,
            "Position Creation": start_time
        }

        table = DFTable(QFDataFrame.from_dict(data), css_classes=['table', 'left-align'])
        self.document.add_element(table)

    def save(self, report_dir: str = ""):
        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M Current Positions.pdf"
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], report_dir, filename)
