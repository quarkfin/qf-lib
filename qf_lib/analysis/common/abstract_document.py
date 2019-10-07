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

from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.charts.underwater_chart import UnderwaterChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.plotting.decorators.top_drawdown_decorator import TopDrawdownDecorator
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class AbstractDocument(metaclass=ABCMeta):
    """
    Base class for Most PDF document with charts and tables.
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, title: str = "Document Title"):
        self.title = title
        self.document = Document(title)
        self.full_image_size = (8, 2.4)

        # position is linked to the position of axis in tearsheet.mplstyle
        self.full_image_axis_position = (0.07, 0.1, 0.915, 0.80)  # (left, bottom, width, height)
        self.half_image_size = (4, 2.1)
        self.dpi = 400

        self.settings = settings
        self.pdf_exporter = pdf_exporter

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
        logo_path = join(get_starting_dir_abs_path(), self.settings.logo_path)
        company_name = self.settings.company_name

        self.document.add_element(PageHeaderElement(logo_path, company_name, self.title))

    def _get_underwater_chart(self, series: QFSeries):
        underwater_chart = UnderwaterChart(series, rotate_x_axis=True)
        underwater_chart.add_decorator(TopDrawdownDecorator(series, 5))
        underwater_chart.add_decorator(AxesLabelDecorator(y_label="Drawdown"))
        underwater_chart.add_decorator(TitleDecorator("Drawdown"))
        return underwater_chart

    def _get_large_perf_chart(self, series_list):
        return self.__get_perf_chart(series_list, True)

    def _get_small_perf_chart(self, series_list):
        return self.__get_perf_chart(series_list, False)

    def __get_perf_chart(self, series_list, is_large_chart):
        strategy = series_list[0].to_prices(1)  # the main strategy should be the first series
        log_scale = True if strategy[-1] > 5 else False  # use log scale for returns above 500 %

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
        title_decorator = TitleDecorator("Strategy Performance", key="title")
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

    def _get_rolling_chart(self, timeseries):
        days_rolling = int(252 / 2)  # 6M rolling
        step = round(days_rolling / 5)

        tms = timeseries.to_prices(1)
        chart = LineChart(start_x=tms.index[0], end_x=tms.index[-1])
        line_decorator = HorizontalLineDecorator(0, key="h_line", linewidth=1)
        chart.add_decorator(line_decorator)

        legend = LegendDecorator()

        def tot_return(window):
            return PricesSeries(window).total_cumulative_return()

        def volatility(window):
            return get_volatility(PricesSeries(window), Frequency.DAILY)

        functions = [tot_return, volatility]
        names = ['Rolling Return', 'Rolling Volatility']
        for func, name in zip(functions, names):
            rolling = tms.rolling_window(days_rolling, func, step=step)
            rolling_element = DataElementDecorator(rolling)
            chart.add_decorator(rolling_element)
            legend.add_entry(rolling_element, name)

        chart.add_decorator(legend)

        chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter(".0f")))

        left, bottom, width, height = self.full_image_axis_position
        position_decorator = AxesPositionDecorator(left, bottom, width, height)
        chart.add_decorator(position_decorator)
        title_str = "{} - Rolling Stats [{} days]".format(timeseries.name, days_rolling)

        title_decorator = TitleDecorator(title_str, key="title")
        chart.add_decorator(title_decorator)

        return chart

    def _add_statistics_table(self, ta_list: List[TimeseriesAnalysis]):
        table = Table(css_class="table stats-table")

        for ta in ta_list:
            ta.populate_table(table)
        self.document.add_element(table)
