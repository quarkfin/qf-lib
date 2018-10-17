from datetime import datetime
from math import sqrt
from os.path import join

import matplotlib as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.document_exporting import Document, GridElement, ParagraphElement
from qf_lib.common.utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.common.utils.document_exporting.element.table import Table
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.get_sources_root import get_src_root
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.histogram_chart import HistogramChart
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_locator_decorator import AxesLocatorDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator, VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


class TradeAnalysisSheet(object):
    """
    Creates a PDF containing main statistics of the trades
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, trades_df: QFDataFrame,
                 nr_of_assets_traded: int = 1, title: str = "Trades"):
        """
        trades_df
            indexed by consecutive numbers starting at 0.
            contains columns as follows: [ xxx,xxx,xxx,...]
        nr_of_assets_traded
            the model can be used to trade on many instruments at the same time.
            All aggregated trades will be in trades_df
            nr_of_instruments_traded informs on how many instruments at the same time the model was traded.
        title
            title of the document, will be a part of the filename. Do not use special characters
        """
        self.trades_df = trades_df
        self.nr_of_assets_traded = nr_of_assets_traded
        self.returns_of_trades = SimpleReturnsSeries(self.trades_df["Return"])
        self.title = title

        self.document = Document(title)

        # position is linked to the position of axis in tearsheet.mplstyle
        self.half_image_size = (4, 2.2)
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

    def _add_histogram_and_cumulative(self,):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

        perf_chart = self._get_perf_chart()
        grid.add_chart(perf_chart)

        histogram_chart = self._get_histogram_chart()
        grid.add_chart(histogram_chart)

        self.document.add_element(grid)

    def _get_perf_chart(self):
        strategy_tms = self.returns_of_trades.to_prices(1)
        chart = LineChart(start_x=strategy_tms.index[0], end_x=strategy_tms.index[-1])
        line_decorator = HorizontalLineDecorator(1, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)

        series_elem = DataElementDecorator(strategy_tms)
        chart.add_decorator(series_elem)

        title_decorator = TitleDecorator("Alpha Model Performance", key="title")
        chart.add_decorator(title_decorator)
        return chart

    def _get_histogram_chart(self):
        colors = Chart.get_axes_colors()
        chart = HistogramChart(self.returns_of_trades)
        # Format the x-axis so that its labels are shown as a percentage.
        x_axis_formatter = FormatStrFormatter("%.0f%%")
        axes_formatter_decorator = AxesFormatterDecorator(x_major=x_axis_formatter, key="axes_formatter")
        chart.add_decorator(axes_formatter_decorator)
        # Only show whole numbers on the y-axis.
        y_axis_locator = MaxNLocator(integer=True)
        axes_locator_decorator = AxesLocatorDecorator(y_major=y_axis_locator, key="axes_locator")
        chart.add_decorator(axes_locator_decorator)

        # Add an average line.
        avg_line = VerticalLineDecorator(self.returns_of_trades.values.mean(), color=colors[1],
                                         key="average_line_decorator", linestyle="--", alpha=0.8)
        chart.add_decorator(avg_line)

        # Add a legend.
        legend = LegendDecorator(key="legend_decorator")
        legend.add_entry(avg_line, "Mean")
        chart.add_decorator(legend)

        # Add a title.
        title = TitleDecorator("Distribution of Trades", key="title_decorator")
        chart.add_decorator(title)
        chart.add_decorator(AxesLabelDecorator("Return", "Occurrences"))
        return chart

    def _add_statistics_table(self):
        table = Table(column_names=["Measure", "Value"], css_class="table stats-table")

        number_of_trades = self.returns_of_trades.count()
        table.add_row(["Number of trades", number_of_trades])

        period_length = self.trades_df["End_date"].iloc[-1] - self.trades_df["Start_date"].iloc[0]
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

        # System Quality Number
        sqn = self.returns_of_trades.mean() / self.returns_of_trades.std()
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
