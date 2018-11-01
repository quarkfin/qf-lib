from datetime import datetime
from math import sqrt
from os.path import join

import matplotlib as plt

from qf_lib.analysis.breakout_strength.trend_strength import trend_strength, down_trend_strength, up_trend_strength
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.document_exporting import Document, ParagraphElement, ChartElement
from qf_lib.common.utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.common.utils.document_exporting.element.table import Table
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.common.utils.returns.annualise_total_return import annualise_total_return
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
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

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, title: str = "Trend Strength"):
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
        self.title = title
        self.window_len = 128

        self.document = Document(title)

        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (8, 2.4)
        self.dpi = 400

        self.settings = settings
        self.pdf_exporter = pdf_exporter

    def build_document(self):
        self._add_header()

        self.document.add_element(ParagraphElement("\n"))
        self._add_histogram_and_cumulative()
        self._add_statistics_table()

    def _add_header(self):
        logo_path = join(get_src_root(), self.settings.logo_path)
        company_name = self.settings.company_name

        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _insert_table_with_overall_measures(self, prices_df: QFDataFrame, ticker: Ticker):
        table = Table(column_names=["Measure", "Value"], css_class="table stats-table")

        table.add_row(["Instrument", ticker.as_string()])
        table.add_row(["Start date", ])
        table.add_row(["End date", ])

        table.add_row(["Overall strength of the day trends", trend_strength(prices_df)])
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

    def _add_statistics_table(self):
        table = Table(column_names=["Measure", "Value"], css_class="table stats-table")

        number_of_trades = self.returns_of_trades.count()
        table.add_row(["Number of trades", number_of_trades])

        period_length = self.trades_df[TradeField.EndDate].iloc[-1] - self.trades_df[TradeField.StartDate].iloc[0]
        period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG
        avg_number_of_trades = number_of_trades / period_length_in_years / self.nr_of_assets_traded
        table.add_row(["Avg number of trades per year per asset", avg_number_of_trades])

        positive_trades = self.returns_of_trades[self.returns_of_trades > 0]
        negative_trades = self.returns_of_trades[self.returns_of_trades < 0]

        percentage_of_positive = positive_trades.count() / number_of_trades
        percentage_of_negative = negative_trades.count() / number_of_trades
        table.add_row(["% of positive trades", percentage_of_positive * 100])
        table.add_row(["% of negative trades", percentage_of_negative * 100])

        avg_positive = positive_trades.mean()
        avg_negative = negative_trades.mean()
        table.add_row(["Avg positive trade [%]", avg_positive * 100])
        table.add_row(["Avg negative trade [%]", avg_negative * 100])

        best_return = max(self.returns_of_trades)
        worst_return = min(self.returns_of_trades)
        table.add_row(["Best trade [%]", best_return * 100])
        table.add_row(["Worst trade [%]", worst_return * 100])

        max_dd = max_drawdown(self.returns_of_trades)
        table.add_row(["Max drawdown [%]", max_dd * 100])

        prices_tms = self.returns_of_trades.to_prices()
        total_return = prices_tms.iloc[-1] / prices_tms.iloc[0] - 1
        table.add_row(["Total return [%]", total_return * 100])

        annualised_ret = annualise_total_return(total_return, period_length_in_years, SimpleReturnsSeries)
        table.add_row(["Annualised return [%]", annualised_ret * 100])

        avg_return = self.returns_of_trades.mean()
        table.add_row(["Avg return of trade [%]", avg_return * 100])

        std_of_returns = self.returns_of_trades.std()
        table.add_row(["Std of return of trades [%]", std_of_returns * 100])

        # System Quality Number
        sqn = avg_return / std_of_returns
        table.add_row(["SQN", sqn])
        table.add_row(["SQN for 100 trades", sqn * 10])  # SQN * sqrt(100)
        table.add_row(["SQN * Sqrt(avg nr. of trades per year)", sqn * sqrt(avg_number_of_trades)])

        self.document.add_element(table)

    def save(self):
        output_sub_dir = "trades_analysis"

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], output_sub_dir, filename)
