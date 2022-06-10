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
from typing import List

from matplotlib.rcsetup import cycler
import pandas as pd
from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.fill_between_decorator import FillBetweenDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings
import matplotlib as plt
from datetime import datetime


@ErrorHandling.class_error_logging()
class FactorComparisonSheet(AbstractDocument):
    """Creates a PDF report

    Parameters
    ----------
    settings: Settings
        settings of the project
    pdf_exporter: PDFExporter
        tool that creates the pdf with the result
    factors_series: list[QFSeries]
        list of timeseries with factors' indices. The order of passed series in the list is important,
        and proper charts generation relies on this. The first timeseries, should be top 5% factor,
        second - top 25% factor, etc., and the last series should be bottom 5% factor (interval 0.95-1).
    benchmark_series: QFSeries
        timeseries of the benchmark
    title: str
        title of the document
    dpi: int
        Determines the DPI (Dots per Inch) of the chart (can be used to control the resolution)
    """
    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, factors_series: List[QFSeries],
                 benchmark_series: QFSeries, title: str = "Factor Comparison", dpi: int = 400):
        super().__init__(settings, pdf_exporter)
        self.factors_series = factors_series
        self.benchmark_series = benchmark_series
        self.title = title
        self.dpi = dpi

    def build_document(self):
        """Creates a document with charts"""
        self._add_header()

        end_date = pd.concat(self.factors_series, axis=1).index.max()
        start_date = end_date - RelativeDelta(years=1)

        all_series_one_year = [self.benchmark_series.loc[start_date:]] + \
                              [series.loc[start_date:] for series in self.factors_series]

        self._add_perf_chart_for_factor(series_list=all_series_one_year,
                                        title="Factors - 1 Year")

        all_series = [self.benchmark_series] + self.factors_series

        self._add_perf_chart_for_factor(series_list=all_series,
                                        title="Factors - Full History",
                                        force_log_scale=True)

        top_factor_tms = self.factors_series[0]
        bottom_factor_tms = self.factors_series[-1]

        self._add_relative_performance_chart_rolling_window(
            top_factor_tms, self.benchmark_series,
            chart_title="Relative Performance Rolling Window 6 Months", legend_subtitle="Top 5% Factor - Benchmark")

        self._add_relative_performance_chart(
            top_factor_tms, bottom_factor_tms,
            chart_title="Relative Performance", legend_subtitle="Top 5% Factor - Bottom 5% Factor")

        for series in self.factors_series:
            self.document.add_element(NewPageElement())
            self._add_header()
            self._add_perf_chart_for_factor(series_list=[self.benchmark_series.loc[start_date:],
                                                         series.loc[start_date:]
                                                         ],
                                            title="{} - 1 Year".format(series.name))
            self._add_relative_performance_chart(
                series.loc[start_date:], self.benchmark_series.loc[start_date:],
                chart_title="Relative Performance", legend_subtitle="Factor - Benchmark")

            self._add_perf_chart_for_factor(series_list=[self.benchmark_series, series],
                                            title="{} - Full History".format(series.name),
                                            force_log_scale=True)
            self.document.add_element(ParagraphElement("\n"))
            self._add_relative_performance_chart(
                series, self.benchmark_series,
                chart_title="Relative Performance", legend_subtitle="Factor - Benchmark")

    def save(self, report_dir: str = ""):
        """Saves document to the file"""
        plt.style.use(['tearsheet'])
        # Change the color map for the plots to use different colors
        hex_colors_fancy = [plt.colors.rgb2hex(c) for c in plt.cm.tab10(range(10))]

        hex_colors = ['#000000', '#ff5757', '#636363', '#969696', '#bdbdbd', '#9ecae1', '#3182bd', *hex_colors_fancy]

        plt.rcParams['axes.prop_cycle'] = cycler(color=hex_colors)

        file_name = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        file_name = datetime.now().strftime(file_name)

        if not file_name.endswith(".pdf"):
            file_name = "{}.pdf".format(file_name)

        return self.pdf_exporter.generate([self.document], report_dir, file_name)

    def _add_perf_chart_for_factor(self, series_list: List[QFSeries], title: str = "Factor Index Performance",
                                   force_log_scale: bool = False):
        """ Add performance chart for factor

        Parameters
        ----------
        series_list: list[QFSeries]
            list of compared series
        title: str
            chart title
        """
        chart = self._get_perf_chart(series_list, is_large_chart=True, title=title)
        if force_log_scale:
            chart.log_scale = True
        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_relative_performance_chart_rolling_window(self, strategy_tms: QFSeries, benchmark_tms: QFSeries,
                                                       chart_title: str = "Relative Performance",
                                                       legend_subtitle: str = "Strategy - Benchmark"):
        diff = strategy_tms.to_simple_returns().subtract(benchmark_tms.to_simple_returns(), fill_value=0)

        def total_cumulative_return(series) -> float:
            return series.total_cumulative_return()

        diff = diff.rolling_window(window_size=128, func=total_cumulative_return, step=5)

        chart = LineChart(start_x=diff.index[0], end_x=diff.index[-1], log_scale=False)
        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        line_decorator = HorizontalLineDecorator(0, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)
        legend = LegendDecorator()

        series_elem = DataElementDecorator(diff)
        chart.add_decorator(series_elem)
        legend.add_entry(series_elem, legend_subtitle)

        chart.add_decorator(legend)
        title_decorator = TitleDecorator(chart_title, key="title")
        chart.add_decorator(title_decorator)

        chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter(".0f")))

        fill_decorator = FillBetweenDecorator(diff)
        chart.add_decorator(fill_decorator)
        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))
