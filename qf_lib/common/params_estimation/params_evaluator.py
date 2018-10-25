from datetime import datetime
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.document_exporting import Document, ChartElement
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
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


class ParamsEvaluator(object):

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter):
        """
        title
            title of the document, will be a part of the filename. Do not use special characters
        """
        self.title = "sample_params_evaluation_title"
        self.document = None
        # position is linked to the position of axis in tearsheet.mplstyle
        self.image_size = (8, 8)
        self.dpi = 400
        self.settings = settings
        self.pdf_exporter = pdf_exporter
        self.backtest_name = ""

    def build_document(self, backtest_result):
        self.title = backtest_result.backtest_name
        self.document = Document(self.title)

        input_dict = {}
        for elem in backtest_result.elements_list:
            input_dict[elem.model_parameters] = elem.trades_df

        if backtest_result.num_of_model_params == 1:
            self._plot_line_chart(input_dict)
        elif backtest_result.num_of_model_params == 2:
            self._plot_single_heat_map(input_dict)
        elif backtest_result.num_of_model_params == 3:
            self._plot_multiple_heat_maps(input_dict)
        else:
            raise ValueError("Incorrect number of parameters. Supported: 1, 2 and 3")

    def _plot_line_chart(self, input_dict: Dict[tuple, QFDataFrame]):

        params = sorted(input_dict.keys())  # this will sort the tuples
        values = []
        for param in params:
            value = self._objective_function(input_dict[param])
            values.append(value)

        params_as_values = [param_tuple[0] for param_tuple in params]
        result_series = QFSeries(data=values, index=params_as_values)

        line_chart = LineChart()
        data_element = DataElementDecorator(result_series)
        line_chart.add_decorator(data_element)
        line_chart.add_decorator(TitleDecorator(self.backtest_name))
        legend = LegendDecorator(legend_placement=Location.BEST, key='legend')
        legend.add_entry(data_element, self.backtest_name)
        line_chart.add_decorator(legend)
        line_chart.add_decorator(AxesLabelDecorator(x_label="Parameter value", y_label="Objective Function"))
        self.document.add_element(ChartElement(line_chart, figsize=self.image_size, dpi=self.dpi))

    def _plot_single_heat_map(self, input_dict: Dict[tuple, QFDataFrame], third_param=None):

        result_df = QFDataFrame()

        for param_tuple, trades_df in input_dict.items():
            row, column = param_tuple
            value = self._objective_function(trades_df)
            result_df.loc[row, column] = value

            result_df.sort_index(axis=0, inplace=True)
            result_df.sort_index(axis=1, inplace=True)

        chart = HeatMapChart(data=result_df, color_map=plt.get_cmap("coolwarm"),
                             min_value=min(result_df.min()), max_value=max(result_df.max()))

        chart.add_decorator(AxisTickLabelsDecorator(labels=list(result_df.columns), axis=Axis.X))
        chart.add_decorator(AxisTickLabelsDecorator(labels=list(reversed(result_df.index)), axis=Axis.Y))
        chart.add_decorator(ValuesAnnotations())
        chart.add_decorator(AxesLabelDecorator(x_label="Parameter 1", y_label="Parameter 2"))

        if third_param is None:
            chart.add_decorator(TitleDecorator(self.backtest_name))
        else:
            chart.add_decorator(TitleDecorator("{}, 3rd param = {:0.2f}".format(self.backtest_name, third_param)))

        self.document.add_element(ChartElement(chart, figsize=self.image_size, dpi=self.dpi))

    def _plot_multiple_heat_maps(self, input_dict: Dict[tuple, QFDataFrame]):
        raise NotImplementedError("Method not implemented for 3 parameters")

    def _objective_function(self, trades: QFDataFrame):
        returns = trades[TradeField.Return]

        period_length = trades[TradeField.EndDate].iloc[-1] - trades[TradeField.StartDate].iloc[0]
        period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG
        avg_number_of_trades_1y = returns.count() / period_length_in_years

        sqn = returns.mean() / returns.std()
        sqn = sqn * np.sqrt(avg_number_of_trades_1y)
        return sqn

    def save(self):
        output_sub_dir = "param_estimation"

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        self.pdf_exporter.generate([self.document], output_sub_dir, filename)