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

from abc import abstractmethod, ABCMeta
from os.path import join
from typing import List

import pandas as pd

from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.plotting.decorators.underwater_decorator import UnderwaterDecorator
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path
from qf_lib.plotting.decorators.fill_between_decorator import FillBetweenDecorator
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement


class AbstractDocument(metaclass=ABCMeta):
    """
    Base class for most PDF documents with charts and tables.

    Parameters
    -----------
    settings: Settings
        settings containing all necessary information
    pdf_exporter: PDFExporter
        used to create PDF document
    title: str
        title of the document
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, title: str = "Document Title"):
        self.title = title
        self.document = Document(title)
        self.full_image_size = (8, 2.4)

        # position is linked to the position of axis in tearsheet.mplstyle
        self.full_image_axis_position = (0.07, 0.1, 0.93, 0.80)  # (left, bottom, width, height)
        self.half_image_size = (4, 2.1)
        self.dpi = 400

        self.settings = settings
        self.pdf_exporter = pdf_exporter
        self.logger = qf_logger.getChild(self.__class__.__name__)

    @abstractmethod
    def build_document(self):
        # main function that composes the document
        pass

    @abstractmethod
    def save(self, report_dir: str = ""):
        # function that saves the document on the disk
        pass

    def _get_new_grid(self) -> GridElement:
        return GridElement(mode=PlottingMode.PDF, figsize=self.half_image_size, dpi=self.dpi)

    def _add_header(self):
        logo_path = join(get_starting_dir_abs_path(), self.settings.logo_path) if hasattr(self.settings, "logo_path") \
            else None
        company_name = getattr(self.settings, "company_name", "")

        if not logo_path:
            self.logger.warning(
                f"{self.__class__.__name__} will be generated without a logo in the header. If you would "
                f"like to include your logo, add 'logo_path' variable to your JSON settings file. "
            )

        if not company_name:
            self.logger.warning(
                f"{self.__class__.__name__} will be generated without a company name in the header. If you would "
                f"like to include your company name, add 'company_name' variable to your JSON settings file. "
            )

        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _get_underwater_chart(self, series: QFSeries, title="Drawdown", benchmark_series: QFSeries = None,
                              rotate_x_axis: bool = False):
        underwater_chart = LineChart(start_x=series.index[0], end_x=series.index[-1], log_scale=False,
                                     rotate_x_axis=rotate_x_axis)
        underwater_chart.add_decorator(UnderwaterDecorator(series))
        underwater_chart.add_decorator(TitleDecorator(title))

        if benchmark_series is not None:
            legend = LegendDecorator()
            benchmark_dd = PricesSeries(drawdown_tms(benchmark_series))
            benchmark_dd *= -1
            benchmark_dd_elem = DataElementDecorator(benchmark_dd, color="black", linewidth=0.5)
            legend.add_entry(benchmark_dd_elem, "Benchmark DD")
            underwater_chart.add_decorator(benchmark_dd_elem)
            underwater_chart.add_decorator(legend)
        return underwater_chart

    def _get_large_perf_chart(self, series_list):
        return self._get_perf_chart(series_list, True)

    def _get_small_perf_chart(self, series_list):
        return self._get_perf_chart(series_list, False)

    def _get_perf_chart(self, series_list, is_large_chart, title="Strategy Performance"):
        strategy = series_list[0].to_prices(1)  # the main strategy should be the first series
        log_scale = True if strategy[-1] > 10 else False  # use log scale for returns above 1 000 %

        if is_large_chart:
            chart = LineChart(start_x=strategy.index[0], end_x=strategy.index[-1], log_scale=log_scale)
            position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
            chart.add_decorator(position_decorator)
        else:
            chart = LineChart(log_scale=log_scale, rotate_x_axis=True)

        line_decorator = HorizontalLineDecorator(1, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)
        legend = LegendDecorator()
        for series in series_list:
            strategy_tms = series.to_prices(1)
            series_elem = DataElementDecorator(strategy_tms)
            chart.add_decorator(series_elem)
            legend.add_entry(series_elem, strategy_tms.name)

        chart.add_decorator(legend)
        title_decorator = TitleDecorator(title, key="title")
        chart.add_decorator(title_decorator)

        return chart

    def _get_leverage_chart(self, leverage: QFSeries, rotate_x_axis: bool = False):
        return self._get_line_chart(leverage, "Leverage over time", rotate_x_axis)

    def _get_line_chart(self, series: QFSeries, title: str, rotate_x_axis: bool = False):
        chart = LineChart(rotate_x_axis=rotate_x_axis)

        series_elem = DataElementDecorator(series)
        chart.add_decorator(series_elem)

        title_decorator = TitleDecorator(title, key="title")
        chart.add_decorator(title_decorator)
        return chart

    def _get_rolling_ret_and_vol_chart(self, timeseries):
        freq = timeseries.get_frequency()

        rolling_window_len = int(freq.value / 2)  # 6M rolling
        step = round(freq.value / 6)  # 2M shift

        tms = timeseries.to_prices(1)
        chart = LineChart(start_x=tms.index[0], end_x=tms.index[-1])
        line_decorator = HorizontalLineDecorator(0, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)

        legend = LegendDecorator()

        def tot_return(window):
            return PricesSeries(window).total_cumulative_return()

        def volatility(window):
            return get_volatility(PricesSeries(window), freq)

        functions = [tot_return, volatility]
        names = ['Rolling Return', 'Rolling Volatility']
        for func, name in zip(functions, names):
            rolling = tms.rolling_window(rolling_window_len, func, step=step)
            rolling_element = DataElementDecorator(rolling)
            chart.add_decorator(rolling_element)
            legend.add_entry(rolling_element, name)

        chart.add_decorator(legend)
        chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter(".0f")))

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)
        title_str = "Rolling Stats [{} {} samples]".format(rolling_window_len, freq)

        title_decorator = TitleDecorator(title_str, key="title")
        chart.add_decorator(title_decorator)
        return chart

    def _get_rolling_chart(self, timeseries_list, rolling_function, function_name):
        freq = timeseries_list[0].get_frequency()
        timeseries_list = [tms.dropna().to_prices(1) for tms in timeseries_list]
        df = pd.concat(timeseries_list, axis=1).fillna(method='ffill')

        rolling_window_len = int(freq.value / 2)  # 6M rolling
        step = round(freq.value / 6)  # 2M shift

        legend = LegendDecorator()

        chart = LineChart(start_x=df.index[0], end_x=df.index[-1])
        line_decorator = HorizontalLineDecorator(0, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)

        for _, tms in df.iteritems():
            rolling = tms.rolling_window(rolling_window_len, rolling_function, step=step)
            rolling_element = DataElementDecorator(rolling)
            chart.add_decorator(rolling_element)
            legend.add_entry(rolling_element, tms.name)

        chart.add_decorator(legend)
        chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter(".0f")))

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)
        title_str = "{} - Rolling Stats [{} {} samples]".format(function_name, rolling_window_len, freq)

        title_decorator = TitleDecorator(title_str, key="title")
        chart.add_decorator(title_decorator)
        return chart

    def _add_statistics_table(self, ta_list: List[TimeseriesAnalysis]):
        table = Table(css_class="table stats-table")

        for ta in ta_list:
            ta.populate_table(table)
        self.document.add_element(table)

    def _add_relative_performance_chart(self, strategy_tms: QFSeries, benchmark_tms: QFSeries,
                                        chart_title: str = "Relative Performance",
                                        legend_subtitle: str = "Strategy - Benchmark"):
        diff = strategy_tms.to_simple_returns().subtract(benchmark_tms.to_simple_returns())
        diff = diff.fillna(0)
        diff = diff.to_prices(1) - 1

        chart = LineChart(start_x=diff.index[0], end_x=diff.index[-1], log_scale=False)
        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        line_decorator = HorizontalLineDecorator(0, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)
        legend = LegendDecorator()

        series_elem = DataElementDecorator(diff)
        chart.add_decorator(series_elem)
        legend.add_entry(series_elem, f"[{legend_subtitle}] % diff")

        title_decorator = TitleDecorator(chart_title, key="title")
        chart.add_decorator(title_decorator)

        chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter(".0f")))

        diff_simple = strategy_tms.to_prices(1).subtract(benchmark_tms.to_prices(1))
        diff_simple = diff_simple.ffill()

        fill_decorator = FillBetweenDecorator(diff_simple)
        chart.add_decorator(fill_decorator)
        legend.add_entry(fill_decorator, f"[{legend_subtitle}] $ diff")

        chart.add_decorator(legend)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))
