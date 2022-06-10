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
from os.path import join
from typing import Sequence

import matplotlib as plt

from qf_lib.analysis.breakout_strength.trend_strength import trend_strength, down_trend_strength, up_trend_strength
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class TrendStrengthSheet:
    """
    Creates a PDF containing main statistics of strength of a day trend.

    Parameters
    -----------
    settings: Settings
        settings containing header information (should contain company_name and logo_path)
    pdf_exporter: PDFExporter
        used to create PDF document
    price_provider: DataProvider
        data provider used to download prices
    window_len: int
        size of window used in rolling windows
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, price_provider: DataProvider, window_len=128):
        self.settings = settings
        self.pdf_exporter = pdf_exporter
        self.price_provider = price_provider
        self.window_len = window_len

        self.start_date = None
        self.end_date = None
        self.title = None
        self.document = None
        self.tickers = None
        self.ticker_to_trend_dict = None

        # if True, the daily trend will be calculated from Open to Open of the next day,
        # if False, the daily trend will be calculated from Open to Close of the same day
        self.use_next_open_instead_of_close = None

        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (8, 2.4)
        self.full_image_axis_position = (0.06, 0.1, 0.94, 0.80)
        self.dpi = 400

    def build_document(self, tickers: Sequence[Ticker], start_date: datetime, end_date: datetime,
                       use_next_open_instead_of_close=False, title="Trend Strength"):
        """Build the document.

        Parameters
        --------------
        tickers: Sequence[Ticker]
            tickers of all tested instruments
        start_date: datetime
            start date of the study
        end_date: datetime
            end date of the study
        use_next_open_instead_of_close: bool
            if True, the daily trend will be calculated from Open to Open of the next day,
            if False, the daily trend will be calculated from Open to Close of the same day
        title: str
            title of the document to be created
        """
        self.use_next_open_instead_of_close = use_next_open_instead_of_close

        suffix = "O-O" if use_next_open_instead_of_close else "O-C"
        self.title = "{} {}".format(title, suffix)

        self.tickers = tickers
        self.document = Document(title)
        self.start_date = start_date
        self.end_date = end_date
        self.ticker_to_trend_dict = {}

        for ticker in self.tickers:
            try:
                self._add_page(ticker)
                print("Finished evaluating trend strength of:  {}".format(ticker.as_string()))
            except Exception:
                print("Error while processing {}".format(ticker.as_string()))

        self._add_summary()

    def _add_page(self, ticker: Ticker):
        self._add_header()

        self.document.add_element(ParagraphElement("\n"))
        self.document.add_element(HeadingElement(2, ticker.as_string()))
        self.document.add_element(ParagraphElement("\n"))

        price_df = self.price_provider.get_price(ticker, PriceField.ohlcv(), self.start_date, self.end_date)

        self._insert_table_with_overall_measures(price_df, ticker)
        self.document.add_element(ParagraphElement("\n"))

        self._add_price_chart(price_df)
        self.document.add_element(ParagraphElement("\n"))

        self._add_trend_strength_chart(price_df)
        self.document.add_element(ParagraphElement("\n"))

        self._add_up_and_down_trend_strength(price_df)
        self.document.add_element(NewPageElement())  # add page break

    def _add_header(self):
        logo_path = join(get_starting_dir_abs_path(), self.settings.logo_path)
        company_name = self.settings.company_name
        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _insert_table_with_overall_measures(self, prices_df: PricesDataFrame, ticker: Ticker):
        table = Table(column_names=["Measure", "Value"], css_class="table stats-table")

        table.add_row(["Instrument", ticker.as_string()])
        series = prices_df[PriceField.Close]
        table.add_row(["Start date", date_to_str(series.index[0])])
        table.add_row(["End date", date_to_str(series.index[-1])])

        trend_strength_overall = trend_strength(prices_df, self.use_next_open_instead_of_close)
        table.add_row(["Overall strength of the day trends", trend_strength_overall])

        trend_strength_1y = trend_strength(prices_df.tail(252), self.use_next_open_instead_of_close)
        table.add_row(["Strength of the day trends in last 1Y", trend_strength_1y])
        self.ticker_to_trend_dict[ticker] = (trend_strength_1y, trend_strength_overall)

        table.add_row(["Up trends strength", up_trend_strength(prices_df, self.use_next_open_instead_of_close)])
        table.add_row(["Down trends strength", down_trend_strength(prices_df, self.use_next_open_instead_of_close)])
        self.document.add_element(table)

    def _add_price_chart(self, prices_df: QFDataFrame):
        close_tms = prices_df[PriceField.Close]
        price_tms = close_tms.to_prices(1)
        chart = LineChart(start_x=price_tms.index[0], end_x=price_tms.index[-1])
        price_elem = DataElementDecorator(price_tms)
        chart.add_decorator(price_elem)
        line_decorator = HorizontalLineDecorator(1, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)
        legend = LegendDecorator()
        legend.add_entry(price_elem, "Close Price")
        chart.add_decorator(legend)
        title_decorator = TitleDecorator("Price of the instrument", key="title")
        chart.add_decorator(title_decorator)
        self._add_axes_position_decorator(chart)
        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_trend_strength_chart(self, prices_df: QFDataFrame):

        def _fun(df):
            return trend_strength(df, self.use_next_open_instead_of_close)

        trend_strength_tms = prices_df.rolling_time_window(window_length=self.window_len, step=1, func=_fun)

        chart = LineChart()
        trend_elem = DataElementDecorator(trend_strength_tms, color='black')
        chart.add_decorator(trend_elem)
        legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
        legend.add_entry(trend_elem, 'Trend strength')
        chart.add_decorator(legend)
        title_decorator = TitleDecorator("Strength of the trend - rolling {} days".format(self.window_len), key="title")
        chart.add_decorator(title_decorator)
        self._add_axes_position_decorator(chart)
        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_up_and_down_trend_strength(self, prices_df: QFDataFrame):
        def _down_trend_fun(df):
            return down_trend_strength(df, self.use_next_open_instead_of_close)

        def _up_trend_fun(df):
            return up_trend_strength(df, self.use_next_open_instead_of_close)

        up_trend_strength_tms = prices_df.rolling_time_window(window_length=self.window_len, step=1,
                                                              func=_down_trend_fun)
        down_trend_strength_tms = prices_df.rolling_time_window(window_length=self.window_len, step=1,
                                                                func=_up_trend_fun)
        chart = LineChart()
        up_trend_elem = DataElementDecorator(up_trend_strength_tms)
        down_trend_elem = DataElementDecorator(down_trend_strength_tms)
        chart.add_decorator(up_trend_elem)
        chart.add_decorator(down_trend_elem)
        legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
        legend.add_entry(up_trend_elem, 'Up trend strength')
        legend.add_entry(down_trend_elem, 'Down trend strength')
        chart.add_decorator(legend)
        title = "Strength of the up and down trend - rolling {} days".format(self.window_len)
        title_decorator = TitleDecorator(title, key="title")
        chart.add_decorator(title_decorator)
        self._add_axes_position_decorator(chart)
        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_summary(self):
        self.document.add_element(ParagraphElement("\n"))
        self.document.add_element(HeadingElement(2, "Summary"))
        self.document.add_element(ParagraphElement("\n"))

        self.document.add_element(ParagraphElement("1Y strength  -  Overall strength - Ticker\n"))

        pairs_sorted_by_value = sorted(self.ticker_to_trend_dict.items(), key=lambda pair: pair[1], reverse=True)

        for ticker, trend_strength_values in pairs_sorted_by_value:
            paragraph_str = "{:12.3f} - {:12.3f} - {}".format(
                trend_strength_values[0], trend_strength_values[1], ticker.as_string())
            self.document.add_element(ParagraphElement(paragraph_str))

    def _add_axes_position_decorator(self, chart: Chart):
        left, bottom, width, height = self.full_image_axis_position
        position_decorator = AxesPositionDecorator(left, bottom, width, height)
        chart.add_decorator(position_decorator)

    def save(self):
        output_sub_dir = "trend_strength"

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], output_sub_dir, filename)
