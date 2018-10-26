from datetime import datetime
from itertools import groupby
from typing import Dict, Callable, Any
from os.path import join

import matplotlib.pyplot as plt
import numpy as np

from geneva_analytics.backtesting.alpha_models_testers.backtest_summary import BacktestSummary
from get_sources_root import get_src_root
from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.document_exporting import Document, ChartElement
from qf_lib.common.utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.heatmap.heatmap_chart import HeatMapChart
from qf_lib.plotting.charts.heatmap.values_annotations import ValuesAnnotations
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


class ParamsEvaluator(object):

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter):
        self.backtest_result = None
        self.document = None
        self.tickers_tested = None

        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (7, 7)
        self.dpi = 400
        self.settings = settings
        self.pdf_exporter = pdf_exporter

    def build_document(self, backtest_result: BacktestSummary):
        self.backtest_result = backtest_result
        self.document = Document(backtest_result.backtest_name)
        self.tickers_tested = backtest_result.tickers

        self._add_header()
        input_dict = {}
        for elem in backtest_result.elements_list:
            input_dict[elem.model_parameters] = elem.trades_df

        if backtest_result.num_of_model_params == 1:
            chart_adding_function = self._add_line_chart
        elif backtest_result.num_of_model_params == 2:
            chart_adding_function = self._add_single_heat_map
        elif backtest_result.num_of_model_params == 3:
            chart_adding_function = self._add_multiple_heat_maps
        else:
            raise ValueError("Incorrect number of parameters. Supported: 1, 2 and 3")

        self._create_charts(input_dict, chart_adding_function)

    def _create_charts(self, input_dict: Dict[tuple, QFDataFrame], char_adding_function: Callable[[Any], None]):
        # create a chart for all trades of all tickers traded
        char_adding_function(input_dict)

        for ticker in self.tickers_tested:
            # create a chart for single ticker
            char_adding_function(input_dict, ticker=ticker)

    def _add_header(self):
        logo_path = join(get_src_root(), self.settings.logo_path)
        company_name = self.settings.company_name
        self.document.add_element(PageHeaderElement(logo_path, company_name, self.backtest_result.backtest_name))

    def _add_line_chart(self, input_dict: Dict[tuple, QFDataFrame], ticker: Ticker=None):
        params = sorted(input_dict.keys())  # this will sort the tuples
        values = []  # stores values of the objective function

        for param in params:
            trades = self._select_trades_of_ticker(input_dict[param], ticker)
            value = self._objective_function(trades)
            values.append(value)

        params_as_values = [param_tuple[0] for param_tuple in params]
        result_series = QFSeries(data=values, index=params_as_values)

        line_chart = LineChart()
        data_element = DataElementDecorator(result_series)
        line_chart.add_decorator(data_element)
        line_chart.add_decorator(TitleDecorator(self._get_chart_title(ticker)))
        line_chart.add_decorator(AxesLabelDecorator(x_label="Parameter value", y_label="Objective Function"))
        self.document.add_element(ChartElement(line_chart, figsize=self.image_size, dpi=self.dpi))

    def _add_single_heat_map(self, input_dict: Dict[tuple, QFDataFrame], ticker: Ticker=None, third_param=None):
        result_df = QFDataFrame()

        for param_tuple, trades_df in input_dict.items():
            row, column = param_tuple
            trades = self._select_trades_of_ticker(input_dict[param_tuple], ticker)
            value = self._objective_function(trades)
            result_df.loc[row, column] = value

            result_df.sort_index(axis=0, inplace=True, ascending=False)
            result_df.sort_index(axis=1, inplace=True)

        chart = HeatMapChart(data=result_df, color_map=plt.get_cmap("coolwarm"),
                             min_value=min(result_df.min()), max_value=max(result_df.max()))

        chart.add_decorator(AxisTickLabelsDecorator(labels=list(result_df.columns), axis=Axis.X))
        chart.add_decorator(AxisTickLabelsDecorator(labels=list(reversed(result_df.index)), axis=Axis.Y))
        chart.add_decorator(ValuesAnnotations())
        chart.add_decorator(AxesLabelDecorator(x_label="Parameter 1", y_label="Parameter 2"))

        if third_param is None:
            title = self._get_chart_title(ticker)
        else:
            title = "{}, 3rd param = {:0.2f}".format(self._get_chart_title(ticker), third_param)
        chart.add_decorator(TitleDecorator(title))

        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _add_multiple_heat_maps(self, input_dict: Dict[tuple, QFDataFrame], ticker: Ticker=None):
        # first sort by the third element of the parameters tuple
        # it is necessary for groupby to work correctly
        sorted_dict = sorted(input_dict.items(), key=lambda x: x[0][2])

        for third_param, group in groupby(sorted_dict, lambda x: x[0][2]):
            # group is a structure: (three_elem_tuple, data_frame) where all third elements of the tuple are the same
            # we want extract the first 2 elements of the tuple to pass it to the _add_single_heat_map method
            two_elem_tuple_to_df_dict = {three_elem_tuple[:2]: df for three_elem_tuple, df in group}
            self._add_single_heat_map(two_elem_tuple_to_df_dict, ticker, third_param=third_param)

    def _get_chart_title(self, ticker):
        backtest_name = self.backtest_result.backtest_name
        if ticker is None:
            title = "{} - All Tickers".format(backtest_name)
        else:
            title = "{} - {}".format(backtest_name, ticker.as_string())
        return title

    def _select_trades_of_ticker(self, trades: QFDataFrame, ticker: Ticker):
        """
        Select only the trades generated by the ticker provided
        If ticker is not provided (None) return all the trades
        """
        if ticker is not None:
            trades = trades.loc[trades[TradeField.Ticker] == ticker]
        return trades

    def _objective_function(self, trades: QFDataFrame):
        """
        Calculates the SQN * sqrt(average number of trades per year)
        """

        number_of_instruments_traded = trades[TradeField.Ticker].unique().size
        returns = trades[TradeField.Return]

        period_length = self.backtest_result.end_date - self.backtest_result.start_date
        period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG
        avg_number_of_trades_1y = returns.count() / period_length_in_years / number_of_instruments_traded

        sqn = returns.mean() / returns.std()
        sqn = sqn * np.sqrt(avg_number_of_trades_1y)
        return sqn

    def save(self):
        if self.document is not None:
            output_sub_dir = "param_estimation"

            # Set the style for the report
            plt.style.use(['tearsheet'])

            filename = "%Y_%m_%d-%H%M {}.pdf".format(self.backtest_result.backtest_name)
            filename = datetime.now().strftime(filename)
            self.pdf_exporter.generate([self.document], output_sub_dir, filename)
        else:
            raise AssertionError("The documnent is not initialized. Build the document first")
