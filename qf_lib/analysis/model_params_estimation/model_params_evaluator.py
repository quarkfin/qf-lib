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
import inspect
from collections import defaultdict
from datetime import datetime
from os.path import join
from typing import Sequence, Optional

import matplotlib.pyplot as plt

from qf_lib.analysis.model_params_estimation.evaluation_utils import BacktestSummaryEvaluator, TradesEvaluationResult
from qf_lib.backtesting.fast_alpha_model_tester.backtest_summary import BacktestSummary
from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.custom import CustomElement
from qf_lib.documents_utils.document_exporting.element.grid import GridElement
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.page_header import PageHeaderElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.heatmap.heatmap_chart import HeatMapChart
from qf_lib.plotting.charts.heatmap.values_annotations import ValuesAnnotations
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


@ErrorHandling.class_error_logging()
class ModelParamsEvaluationDocument:

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter):
        self.backtest_summary = None
        self.backtest_evaluator = None  # type: BacktestSummaryEvaluator
        self.document = None
        self.out_of_sample_start_date = None  # type: Optional[datetime]

        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (7, 6)
        self.full_image_size = (8, 2.4)
        self.image_axis_position = (0.08, 0.08, 0.92, 0.85)
        self.dpi = 400
        self.settings = settings
        self.pdf_exporter = pdf_exporter

    def build_document(self, backtest_summary: BacktestSummary, out_of_sample_start_date: Optional[datetime] = None):
        self.backtest_summary = backtest_summary
        self.backtest_evaluator = BacktestSummaryEvaluator(backtest_summary)

        self.document = Document(backtest_summary.backtest_name)
        self.out_of_sample_start_date = out_of_sample_start_date if out_of_sample_start_date is not None else \
            (backtest_summary.start_date + (backtest_summary.end_date - backtest_summary.start_date) / 2)

        self._add_header()
        self._add_backtest_description()

        tickers_groups_for_stats_purposes = list(self.backtest_summary.tickers)
        # In case of > 1 ticker in the backtest summary, include also stats for all tickers if possible
        if len(self.backtest_summary.tickers) > 1:
            tickers_groups_for_stats_purposes = [self.backtest_summary.tickers] + tickers_groups_for_stats_purposes

        if backtest_summary.num_of_model_params not in [1, 2]:
            raise ValueError("Incorrect number of parameters. Supported: 1 and 2")

        for tickers in tickers_groups_for_stats_purposes:
            tickers, _ = convert_to_list(tickers, Ticker)
            self.document.add_element(NewPageElement())

            if backtest_summary.num_of_model_params == 1:
                self._add_line_plots(tickers)
            else:
                self._add_heat_maps(tickers)

    def _add_header(self):
        logo_path = join(get_starting_dir_abs_path(), self.settings.logo_path)
        company_name = self.settings.company_name
        self.document.add_element(PageHeaderElement(logo_path, company_name, self.backtest_summary.backtest_name))

    def _add_backtest_description(self):
        """
        Adds verbal description of the backtest to the document. The description will be placed on a single page.
        """
        param_names = self._get_param_names()

        self.document.add_element(HeadingElement(1, "Model: {}".format(self.backtest_summary.backtest_name)))
        self.document.add_element(ParagraphElement("\n"))

        self.document.add_element(HeadingElement(2, "Tickers tested in this study: "))
        ticker_str = "\n".join([ticker.name for ticker in self.backtest_summary.tickers])
        self.document.add_element(ParagraphElement(ticker_str))
        self.document.add_element(ParagraphElement("\n"))

        self.document.add_element(HeadingElement(2, "Dates of the backtest"))
        self.document.add_element(ParagraphElement("Backtest start date: {}"
                                                   .format(date_to_str(self.backtest_summary.start_date))))
        self.document.add_element(ParagraphElement("Backtest end date: {}"
                                                   .format(date_to_str(self.backtest_summary.end_date))))
        self.document.add_element(ParagraphElement("\n"))

        self.document.add_element(HeadingElement(2, "Parameters Tested"))
        for param_index, param_list in enumerate(self.backtest_summary.parameters_tested):
            param_list_str = ", ".join(map(str, param_list))
            self.document.add_element(ParagraphElement("{} = [{}]".format(param_names[param_index], param_list_str)))

        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(2, "Alpha model implementation"))
        self.document.add_element(ParagraphElement("\n"))

        model_type = self.backtest_summary.alpha_model_type
        with open(inspect.getfile(model_type)) as f:
            class_implementation = f.read()
        # Remove the imports section
        class_implementation = "<pre>class {}".format(model_type.__name__) + \
                               class_implementation.split("class {}".format(model_type.__name__))[1] + "</pre>"
        self.document.add_element(CustomElement(class_implementation))

    def _add_line_plots(self, tickers: Sequence[Ticker]):
        parameters_list = sorted(self.backtest_evaluator.params_backtest_summary_elem_dict.keys())

        title_to_plot = defaultdict(lambda: LineChart())
        title_to_legend = defaultdict(lambda: LegendDecorator(key="legend_decorator"))

        for start_time, end_time in [(self.backtest_summary.start_date, self.out_of_sample_start_date),
                                     (self.out_of_sample_start_date, self.backtest_summary.end_date)]:
            results = []

            for param_tuple in parameters_list:
                trades_eval_result = self.backtest_evaluator.evaluate_params_for_tickers(param_tuple, tickers,
                                                                                         start_time, end_time)
                results.append(trades_eval_result)

            sqn_avg_nr_trades = DataElementDecorator([x.sqn_per_avg_nr_trades for x in results])
            avg_nr_of_trades = DataElementDecorator([x.avg_nr_of_trades_1Y for x in results])
            annualised_return = DataElementDecorator([x.annualised_return for x in results])

            adjusted_start_time = min([x.start_date for x in results])
            adjusted_end_time = max([x.end_date for x in results])
            if adjusted_start_time >= adjusted_end_time:
                adjusted_end_time = adjusted_start_time if adjusted_start_time <= self.backtest_summary.end_date \
                    else end_time
                adjusted_start_time = start_time
            title = "{} - {} ".format(adjusted_start_time.strftime("%Y-%m-%d"), adjusted_end_time.strftime("%Y-%m-%d"))

            title_to_plot["SQN (Arithmetic return) per year"].add_decorator(sqn_avg_nr_trades)
            title_to_legend["SQN (Arithmetic return) per year"].add_entry(sqn_avg_nr_trades, title)

            title_to_plot["Avg # trades 1Y"].add_decorator(avg_nr_of_trades)
            title_to_legend["Avg # trades 1Y"].add_entry(sqn_avg_nr_trades, title)

            if len(tickers) == 1:
                title_to_plot["Annualised return"].add_decorator(annualised_return)
                title_to_legend["Annualised return"].add_entry(annualised_return, title)

        tickers_used = "Many tickers" if len(tickers) > 1 else (
            tickers[0].name
        )

        for description, line_chart in title_to_plot.items():
            self.document.add_element(HeadingElement(3, "{} - {}".format(description, tickers_used)))
            line_chart.add_decorator(AxesLabelDecorator(x_label=self._get_param_names()[0], y_label=title))
            position_decorator = AxesPositionDecorator(*self.image_axis_position)
            line_chart.add_decorator(position_decorator)
            legend = title_to_legend[description]
            line_chart.add_decorator(legend)
            self.document.add_element(ChartElement(line_chart, figsize=self.full_image_size))

    def _add_heat_maps(self, tickers: Sequence[Ticker]):
        parameters_list = sorted(self.backtest_evaluator.params_backtest_summary_elem_dict.keys())

        # Group plots by type, so that they appear in the given logical order
        title_to_grid = defaultdict(lambda: GridElement(mode=PlottingMode.PDF, figsize=self.image_size))
        for start_time, end_time in [(self.backtest_summary.start_date, self.out_of_sample_start_date),
                                     (self.out_of_sample_start_date, self.backtest_summary.end_date)]:
            results = QFDataFrame()

            for param_tuple in parameters_list:
                trades_eval_result = self.backtest_evaluator.evaluate_params_for_tickers(param_tuple, tickers,
                                                                                         start_time, end_time)
                row, column = param_tuple
                results.loc[row, column] = trades_eval_result

            results.sort_index(axis=0, inplace=True, ascending=False)
            results.sort_index(axis=1, inplace=True)
            results.fillna(TradesEvaluationResult(), inplace=True)

            sqn_avg_nr_trades = results.applymap(lambda x: x.sqn_per_avg_nr_trades).fillna(0)
            avg_nr_of_trades = results.applymap(lambda x: x.avg_nr_of_trades_1Y).fillna(0)
            annualised_return = results.applymap(lambda x: x.annualised_return).fillna(0)

            adjusted_start_time = results.applymap(lambda x: x.start_date).min().min()
            adjusted_end_time = results.applymap(lambda x: x.end_date).max().max()
            if adjusted_start_time >= adjusted_end_time:
                adjusted_end_time = adjusted_start_time if adjusted_start_time <= self.backtest_summary.end_date \
                    else end_time
                adjusted_start_time = start_time
            title = "{} - {} ".format(adjusted_start_time.strftime("%Y-%m-%d"), adjusted_end_time.strftime("%Y-%m-%d"))

            title_to_grid["SQN (Arithmetic return) per year"].add_chart(
                self._create_single_heat_map(title, sqn_avg_nr_trades, 0, 0.5))

            title_to_grid["Avg # trades 1Y"].add_chart(
                self._create_single_heat_map(title, avg_nr_of_trades, 2, 15))

            if len(tickers) == 1:
                title_to_grid["Annualised return"].add_chart(
                    self._create_single_heat_map(title, annualised_return, 0.0, 0.3))

        tickers_used = "Many tickers" if len(tickers) > 1 else (
            tickers[0].name
        )

        for description, grid in title_to_grid.items():
            self.document.add_element(HeadingElement(3, "{} - {}".format(description, tickers_used)))
            self.document.add_element(grid)

    def _create_single_heat_map(self, title, result_df, min_v, max_v):
        chart = HeatMapChart(data=result_df, color_map=plt.get_cmap("coolwarm"))
        chart.add_decorator(AxisTickLabelsDecorator(labels=list(result_df.columns), axis=Axis.X))
        chart.add_decorator(AxisTickLabelsDecorator(labels=list(reversed(result_df.index)), axis=Axis.Y))
        chart.add_decorator(ValuesAnnotations())
        param_names = self._get_param_names()
        chart.add_decorator(AxesLabelDecorator(x_label=param_names[1], y_label=param_names[0]))
        chart.add_decorator(TitleDecorator(title))
        position_decorator = AxesPositionDecorator(*self.image_axis_position)
        chart.add_decorator(position_decorator)
        return chart

    def _get_param_names(self):
        model_parameters_names = [tuple(el.model_parameters_names) for el in self.backtest_summary.elements_list]
        assert len(set(model_parameters_names)) == 1, "All parameters should have exactly the same parameters tuples"
        return model_parameters_names[0]

    def save(self, title: Optional[str] = None):
        if self.document is not None:
            output_sub_dir = "param_estimation"

            # Set the style for the report
            plt.style.use(['tearsheet'])
            if title is None:
                title = self.backtest_summary.backtest_name
            filename = "%Y_%m_%d-%H%M {}.pdf".format(title)
            filename = datetime.now().strftime(filename)
            self.pdf_exporter.generate([self.document], output_sub_dir, filename)
        else:
            raise AssertionError("The documnent is not initialized. Build the document first")
