from datetime import datetime
from os.path import join
from typing import Sequence

import matplotlib as plt

from qf_lib.analysis.breakout_strength.trend_strength import trend_strength, down_trend_strength, up_trend_strength
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.document_exporting import ParagraphElement, ChartElement, Document, HeadingElement
from qf_lib.common.utils.document_exporting.element.new_page import NewPageElement
from qf_lib.common.utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.common.utils.document_exporting.element.table import Table
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.price_data_provider import DataProvider
from qf_lib.get_sources_root import get_src_root
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


class TrendStrengthSheet(object):
    """
    Creates a PDF containing main statistics of strength of a day trend
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, price_provider: DataProvider):
        """
        trades_df
            indexed by consecutive numbers starting at 0.
            columns are indexed using TradeField values
        nr_of_assets_traded
            the model can be used to trade on many instruments at the same time.
            All aggregated trades will be in trades_df
            nr_of_instruments_traded informs on how many instruments at the same time the model was traded.
        title
            title of the document, will be a part of the filename. Do not use special characters
        """
        self.settings = settings
        self.pdf_exporter = pdf_exporter
        self.price_provider = price_provider

        self.start_date = None
        self.end_date = None
        self.title = None
        self.document = None
        self.tickers = None
        self.ticker_to_trend_dict = {}

        self.window_len = 128
        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (8, 2.4)
        self.dpi = 400

    def build_document(self, tickers: Sequence[Ticker], start_date: datetime, end_date: datetime, title="Trend Strength"):
        self.tickers = tickers
        self.document = Document(title)
        self.start_date = start_date
        self.end_date = end_date

        for ticker in self.tickers:
            self._add_page(ticker)
            print("Finished evaluating trend strength of:  {}".format(ticker.as_string()))

        self._add_summary()

    def _add_page(self, ticker: Ticker):
        self._add_header()
        self.document.add_element(HeadingElement(2, ticker.as_string()))

        price_df = self.price_provider.get_price(ticker, PriceField.ohlcv(), self.start_date, self.end_date)

        self._insert_table_with_overall_measures(price_df, ticker)
        self._add_price_chart(price_df)
        self._add_trend_strength_chart(price_df)
        self._add_up_and_down_trend_strength(price_df)
        self.document.add_element(NewPageElement())  # add page break

    def _add_header(self):
        logo_path = join(get_src_root(), self.settings.logo_path)
        company_name = self.settings.company_name
        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _insert_table_with_overall_measures(self, prices_df: PricesDataFrame, ticker: Ticker):
        table = Table(column_names=["Measure", "Value"], css_class="table stats-table")

        table.add_row(["Instrument", ticker.as_string()])
        series = prices_df[PriceField.Close]
        table.add_row(["Start date", date_to_str(series.index[0])])
        table.add_row(["End date", date_to_str(series.index[-1])])

        trend_strength_value = trend_strength(prices_df)
        table.add_row(["Overall strength of the day trends", trend_strength_value])
        self.ticker_to_trend_dict[ticker] = trend_strength_value

        table.add_row(["Up trends strength", up_trend_strength(prices_df)])
        table.add_row(["Down trends strength", down_trend_strength(prices_df)])
        self.document.add_element(table)

    def _add_price_chart(self, prices_df: QFDataFrame):
        close_tms = prices_df[PriceField.Close]
        series = close_tms.to_prices(1)
        chart = LineChart(start_x=series.index[0], end_x=series.index[-1])
        line_decorator = HorizontalLineDecorator(1, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)
        legend = LegendDecorator()
        legend.add_entry(series, "Close Price")
        chart.add_decorator(legend)
        title_decorator = TitleDecorator("Price of the instrument", key="title")
        chart.add_decorator(title_decorator)
        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_trend_strength_chart(self, prices_df: QFDataFrame):
        trend_strength_tms = prices_df.rolling_time_window(window_length=self.window_len, step=1, func=trend_strength)
        
        chart = LineChart()
        trend_elem = DataElementDecorator(trend_strength_tms, color='black')
        chart.add_decorator(trend_elem)
        legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
        legend.add_entry(trend_elem, 'Trend strength')
        chart.add_decorator(legend)
        title_decorator = TitleDecorator("Strength of the trend - rolling {} days".format(self.window_len), key="title")
        chart.add_decorator(title_decorator)
        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_up_and_down_trend_strength(self, prices_df: QFDataFrame):
        up_trend_strength_tms = prices_df.rolling_time_window(window_length=self.window_len, step=1,
                                                              func=down_trend_strength)
        down_trend_strength_tms = prices_df.rolling_time_window(window_length=self.window_len, step=1,
                                                                func=up_trend_strength)
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
        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_summary(self):
        self.document.add_element(HeadingElement(2, "Summary"))
        pairs_sorted_by_value = sorted(self.ticker_to_trend_dict.items(), key=lambda pair: pair[1])

        for ticker, trend_strength_value in pairs_sorted_by_value:
            paragraph_str = "{} - {:6.2f}".format(ticker.as_string(), trend_strength_value)
            self.document.add_element(ParagraphElement(paragraph_str))

    def save(self):
        output_sub_dir = "trend_strength"

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], output_sub_dir, filename)




