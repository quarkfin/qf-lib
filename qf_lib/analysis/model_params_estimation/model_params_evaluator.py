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
from inspect import getfullargspec
from itertools import groupby
from os.path import join
from typing import Callable, Any, Sequence

import matplotlib.pyplot as plt

from qf_lib.analysis.model_params_estimation.evaluation_utils import add_backtest_description, BacktestSummaryEvaluator
from qf_lib.backtesting.fast_alpha_model_tester.backtest_summary import BacktestSummary
from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.heatmap.heatmap_chart import HeatMapChart
from qf_lib.plotting.charts.heatmap.values_annotations import ValuesAnnotations
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class ModelParamsEvaluator(object):

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter):
        self.backtest_result = None
        self.backtest_evaluator = None  # type: BacktestSummaryEvaluator
        self.document = None

        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (7, 6)
        self.image_axis_position = (0.08, 0.08, 0.92, 0.85)
        self.dpi = 400
        self.settings = settings
        self.pdf_exporter = pdf_exporter

    def build_document(self, backtest_result: BacktestSummary):
        self.backtest_result = backtest_result
        self.backtest_evaluator = BacktestSummaryEvaluator(backtest_result)
        self.document = Document(backtest_result.backtest_name)

        self._add_header()
        param_names = self._get_param_names()
        add_backtest_description(self.document, self.backtest_result, param_names)

        if backtest_result.num_of_model_params == 1:
            chart_adding_function = self._add_line_chart_grid
        elif backtest_result.num_of_model_params == 2:
            parameters_list = self.backtest_evaluator.params_backtest_summary_elem_dict.keys()

            def fun(tickers):
                return self._add_heat_map_grid(tickers, parameters_list)

            chart_adding_function = fun
        elif backtest_result.num_of_model_params == 3:
            chart_adding_function = self._add_multiple_heat_maps
        else:
            raise ValueError("Incorrect number of parameters. Supported: 1, 2 and 3")

        self._create_charts(chart_adding_function)

    def _create_charts(self, chart_adding_function: Callable[[Any], None]):
        # create a chart for all trades of all tickers traded
        chart_adding_function(tickers=self.backtest_result.tickers)

        for ticker in self.backtest_result.tickers:
            # create a chart for single ticker
            chart_adding_function(tickers=[ticker])

    def _add_header(self):
        logo_path = join(get_starting_dir_abs_path(), self.settings.logo_path)
        company_name = self.settings.company_name
        self.document.add_element(PageHeaderElement(logo_path, company_name, self.backtest_result.backtest_name))

    def _add_line_chart_grid(self, tickers: Sequence[Ticker]):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.image_size)
        params = sorted(self.backtest_evaluator.params_backtest_summary_elem_dict.keys())  # this will sort the tuples
        params_as_values = [param_tuple[0] for param_tuple in params]

        results = []
        for param_tuple in params:
            trades_eval_result = self.backtest_evaluator.evaluate_params_for_tickers(param_tuple, tickers)
            results.append(trades_eval_result)

        sqn_avg_trades = [elem.sqn_per_avg_nr_trades for elem in results]
        sqn_per100trades = [elem.sqn_per100trades for elem in results]
        avg_nr_of_trades = [elem.avg_nr_of_trades_1Y for elem in results]
        annualised_return = [elem.annualised_return for elem in results]
        drawdown = [elem.drawdown for elem in results]

        grid.add_chart(self._crete_single_line_chart("SQN / AVG #trades", params_as_values, sqn_avg_trades, tickers))
        grid.add_chart(self._crete_single_line_chart("SQN / 100 trades", params_as_values, sqn_per100trades, tickers))
        grid.add_chart(self._crete_single_line_chart("Avg # trades 1Y", params_as_values, avg_nr_of_trades, tickers))
        grid.add_chart(self._crete_single_line_chart("An Return", params_as_values, annualised_return, tickers))
        grid.add_chart(self._crete_single_line_chart("Drawdown", params_as_values, drawdown, tickers))

        self.document.add_element(grid)

    def _crete_single_line_chart(self, measure_name, parameters, values, tickers):
        result_series = QFSeries(data=values, index=parameters)
        line_chart = LineChart()
        data_element = DataElementDecorator(result_series)
        line_chart.add_decorator(data_element)
        line_chart.add_decorator(TitleDecorator(self._get_chart_title(tickers, measure_name)))
        param_names = self._get_param_names()
        line_chart.add_decorator(AxesLabelDecorator(x_label=param_names[0], y_label=measure_name))
        self._resize_chart(line_chart)
        return line_chart

    def _add_heat_map_grid(self, tickers: Sequence[Ticker], parameters_list: Sequence[tuple], third_param=None):
        grid = GridElement(mode=PlottingMode.PDF, figsize=self.image_size)
        result_df = QFDataFrame()

        for param_tuple in parameters_list:
            row = param_tuple[0]
            column = param_tuple[1]
            trades_eval_result = self.backtest_evaluator.evaluate_params_for_tickers(param_tuple, tickers)
            result_df.loc[row, column] = trades_eval_result

        result_df.sort_index(axis=0, inplace=True, ascending=False)
        result_df.sort_index(axis=1, inplace=True)

        sqn_avg_nr_trades = result_df.applymap(lambda x: x.sqn_per_avg_nr_trades)
        sqn_per100trades = result_df.applymap(lambda x: x.sqn_per100trades)
        avg_nr_of_trades = result_df.applymap(lambda x: x.avg_nr_of_trades_1Y)
        annualised_return = result_df.applymap(lambda x: x.annualised_return)
        drawdown = result_df.applymap(lambda x: x.drawdown)

        grid.add_chart(self._create_single_heat_map("SQN / AVG #trades", sqn_avg_nr_trades, tickers, 0, 1, third_param))
        grid.add_chart(self._create_single_heat_map("SQN / 100 trades", sqn_per100trades, tickers, 0, 2, third_param))
        grid.add_chart(self._create_single_heat_map("Avg # trades 1Y", avg_nr_of_trades, tickers, 3, 30, third_param))
        grid.add_chart(self._create_single_heat_map("An Return", annualised_return, tickers, -0.1, 0.2, third_param))
        grid.add_chart(self._create_single_heat_map("Drawdown", drawdown, tickers, -0.5, -0.1, third_param))

        self.document.add_element(grid)

    def _create_single_heat_map(self, measure_name, result_df, tickers, min_v, max_v, third_param):
        chart = HeatMapChart(data=result_df, color_map=plt.get_cmap("coolwarm"), min_value=min_v, max_value=max_v)
        chart.add_decorator(AxisTickLabelsDecorator(labels=list(result_df.columns), axis=Axis.X))
        chart.add_decorator(AxisTickLabelsDecorator(labels=list(reversed(result_df.index)), axis=Axis.Y))
        chart.add_decorator(ValuesAnnotations())
        param_names = self._get_param_names()
        chart.add_decorator(AxesLabelDecorator(x_label=param_names[1], y_label=param_names[0]))
        if third_param is None:
            title = self._get_chart_title(tickers, measure_name)
        else:
            title = "{}, {} = {:0.2f}".format(self._get_chart_title(tickers, measure_name), param_names[2], third_param)
        chart.add_decorator(TitleDecorator(title))
        self._resize_chart(chart)
        return chart

    def _resize_chart(self, chart):
        left, bottom, width, height = self.image_axis_position
        position_decorator = AxesPositionDecorator(left, bottom, width, height)
        chart.add_decorator(position_decorator)

    def _add_multiple_heat_maps(self, tickers: Sequence[Ticker]):
        parameters_list = self.backtest_evaluator.params_backtest_summary_elem_dict.keys()
        # sort by third parameter, must have for groupby.
        sorted_list = sorted(parameters_list, key=lambda x: x[2])

        for third_param, group in groupby(sorted_list, lambda x: x[2]):
            self._add_heat_map_grid(tickers, group, third_param=third_param)

    def _get_chart_title(self, tickers, measure_name):
        if len(tickers) > 1:
            title = "{} - Many Tickers".format(measure_name)
        elif len(tickers) == 1:
            title = "{} - {}".format(measure_name, tickers[0].as_string())
        else:
            raise ValueError("No tickers provided")
        return title

    def _get_param_names(self):
        names = []
        num_of_params = self.backtest_result.num_of_model_params
        model_type = self.backtest_result.alpha_model_type

        args = getfullargspec(model_type.__init__).args
        if len(args) <= 3:  # alpha model type does not include any parameter fields to evaluate
            for param in range(1, num_of_params + 1):
                names.append("Parameter #{}".format(param))
        else:
            for param in range(1, num_of_params + 1):
                names.append(args[param])

        assert len(names) == self.backtest_result.num_of_model_params
        return names

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
