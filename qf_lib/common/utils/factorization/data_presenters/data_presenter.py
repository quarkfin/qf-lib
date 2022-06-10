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
from itertools import cycle
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.matplotlib_location import Location
from qf_lib.common.enums.orientation import Orientation
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.factorization.data_models.data_model import DataModel
from qf_lib.common.utils.factorization.factors_identification.elastic_net_factors_identifier import \
    ElasticNetFactorsIdentifier
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.heatmap.color_bar import ColorBar
from qf_lib.plotting.charts.heatmap.heatmap_chart import HeatMapChart
from qf_lib.plotting.charts.heatmap.values_annotations import ValuesAnnotations
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.coordinate import DataCoordinate, AxesCoordinate
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.stem_decorator import StemDecorator
from qf_lib.plotting.decorators.text_decorator import TextDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.plotting.decorators.vertical_span_decorator import VerticalSpanDecorator
from qf_lib.plotting.helpers.index_translator import IndexTranslator


class DataPresenter:
    """
    Class used for presenting the data stored in the FactorizationDataModel.
    Parameters
    ----------
    model
        model for the data, which should be presented
    ticker_to_security_name_dict
        dictionary mapping tickers to security names
    """

    def __init__(self, model: DataModel, ticker_to_security_name_dict: Mapping[str, str],
                 enet_factors_identifier: ElasticNetFactorsIdentifier = None):
        self.model = model
        self.ticker_to_security_name_dict = ticker_to_security_name_dict
        self._enet_factors_identifier = enet_factors_identifier
        self._bars_width = 0.5

    def model_info(self) -> str:
        analysed_tms = self.model.input_data.analysed_tms
        regressors_df = self.model.input_data.regressors_df
        fund_name = self._get_security_name(analysed_tms.name)

        iso_date = DateFormat.ISO.format_string
        today_iso_date = datetime.today().strftime(iso_date)
        model_info = '\n=============================================================\n' \
                     '\t Fund name: {}                     {} \n' \
                     '=============================================================\n' \
                     '\t Coefficient \tTicker          Security name\n' \
                     '-------------------------------------------------------------\n'.format(fund_name, today_iso_date)

        for col_nr, ticker in enumerate(regressors_df.columns):
            security_name = self.ticker_to_security_name_dict.get(ticker, "")
            model_info += '\t {:+5.3f}         {:15s} {:s}\n'.format(
                self.model.coefficients[col_nr], ticker, security_name)

        model_info += '\nIntercept is equal to {:4.2f} \n\n'.format(self.model.intercept)

        start_date = analysed_tms.index[0].strftime(iso_date)
        end_date = analysed_tms.index[-1].strftime(iso_date)
        num_of_returns = len(analysed_tms)
        frequency = str(self.model.input_data.frequency)

        model_info += 'The model was build based on {:d} {:s} returns \n' \
                      'between {:s} and {:s}. \n'.format(num_of_returns, frequency, start_date, end_date)

        return model_info

    def get_model_and_fund_statistics(self) -> str:
        statistics = "\nFit R Square = {:5.3f} \n\n" \
                     "{:44s} \t Fit \n".format(self.model.r_squared, self.model.input_data.analysed_tms.name)

        statistics += TimeseriesAnalysis.values_in_table(self.model.fund_tms_analysis)

        return statistics

    def historical_performance_chart(self) -> LineChart:
        frequency = self.model.input_data.frequency
        analysed_tms = self.model.input_data.analysed_tms
        fitted_tms = self.model.fitted_tms

        cumulative_fund_rets = analysed_tms.to_prices(initial_price=1.0, frequency=frequency) - 1
        cumulative_fit_rets = fitted_tms.to_prices(initial_price=1.0, frequency=frequency) - 1

        hist_performance_chart = LineChart()
        fund_cummulative_rets_data_elem = DataElementDecorator(cumulative_fund_rets)
        fit_cummulative_rets_data_elem = DataElementDecorator(cumulative_fit_rets)

        legend_decorator = LegendDecorator(legend_placement=Location.LOWER_RIGHT)
        legend_decorator.add_entry(fund_cummulative_rets_data_elem, self._get_security_name(analysed_tms.name))
        legend_decorator.add_entry(fit_cummulative_rets_data_elem, 'Fit')

        hist_performance_chart.add_decorator(fund_cummulative_rets_data_elem)
        hist_performance_chart.add_decorator(fit_cummulative_rets_data_elem)

        hist_performance_chart.add_decorator(TitleDecorator("Historical Performance"))
        hist_performance_chart.add_decorator(AxesLabelDecorator(y_label="Cumulative return"))
        hist_performance_chart.add_decorator(legend_decorator)
        hist_performance_chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter()))

        return hist_performance_chart

    def historical_out_of_sample_performance_chart(self) -> LineChart:
        analysed_tms = self.model.input_data.analysed_tms
        frequency = self.model.input_data.frequency
        fund_cumulative_rets = analysed_tms.to_prices(
            initial_price=1.0, frequency=frequency) - 1  # type: PricesSeries
        fit_cumulative_rets = self.model.fitted_tms.to_prices(
            initial_price=1.0, frequency=frequency) - 1  # type: PricesSeries

        live_start_date = self.model.oos_start_date

        in_sample_fund_tms = fund_cumulative_rets.loc[:live_start_date]
        in_sample_fit_tms = fit_cumulative_rets.loc[:live_start_date]

        out_of_sample_fund_tms = fund_cumulative_rets.loc[live_start_date:]
        out_of_sample_fit_tms = fit_cumulative_rets.loc[live_start_date:]

        colors = Chart.get_axes_colors()

        in_sample_fund_data_elem = DataElementDecorator(in_sample_fund_tms, color=colors[0])
        out_of_sample_fund_data_elem = DataElementDecorator(out_of_sample_fund_tms, color=colors[0])

        in_sample_fit_data_elem = DataElementDecorator(in_sample_fit_tms, color=colors[1])
        out_of_sample_fit_data_elem = DataElementDecorator(out_of_sample_fit_tms, color=colors[1])

        legend_decorator = LegendDecorator(legend_placement=Location.LOWER_RIGHT)
        legend_decorator.add_entry(in_sample_fund_data_elem, self._get_security_name(analysed_tms.name))
        legend_decorator.add_entry(in_sample_fit_data_elem, 'Fit')

        is_vs_oos_performance_chart = LineChart()
        is_vs_oos_performance_chart.add_decorator(in_sample_fund_data_elem)
        is_vs_oos_performance_chart.add_decorator(out_of_sample_fund_data_elem)
        is_vs_oos_performance_chart.add_decorator(in_sample_fit_data_elem)
        is_vs_oos_performance_chart.add_decorator(out_of_sample_fit_data_elem)

        is_vs_oos_performance_chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter()))
        is_vs_oos_performance_chart.add_decorator(AxesLabelDecorator(y_label="Cumulative return [%]"))
        is_vs_oos_performance_chart.add_decorator(legend_decorator)

        is_vs_oos_performance_chart.add_decorator(TextDecorator("In Sample  ",
                                                                x=DataCoordinate(live_start_date),
                                                                y=AxesCoordinate(0.99),
                                                                verticalalignment='top',
                                                                horizontalalignment='right'))

        is_vs_oos_performance_chart.add_decorator(TextDecorator("  Out Of Sample",
                                                                x=DataCoordinate(live_start_date),
                                                                y=AxesCoordinate(0.99),
                                                                verticalalignment='top', horizontalalignment='left'))
        last_date = fund_cumulative_rets.index[-1]
        is_vs_oos_performance_chart.add_decorator(VerticalSpanDecorator(x_min=live_start_date, x_max=last_date))

        return is_vs_oos_performance_chart

    def beta_and_alpha_chart(self, benchmark_coefficients: Sequence[float] = None) -> BarChart:
        colors_palette = Chart.get_axes_colors()

        coeff_names = [self._get_security_name(ticker) for ticker in self.model.coefficients.index.values]
        coeff_values = self.model.coefficients.values

        bars_colors = [colors_palette[0]] * len(self.model.coefficients)
        title = 'Coefficients of regressors'

        if self.model.input_data.is_fit_intercept:
            coeff_names = np.insert(coeff_names, 0, "intercept")
            coeff_values = np.insert(coeff_values, 0, self.model.intercept)
            bars_colors = ['gold'] + bars_colors

            if benchmark_coefficients is not None:
                raise ValueError("Benchmark coefficients aren't used when model contains a bias value (constant)")
        elif benchmark_coefficients is not None:
            coeff_values -= benchmark_coefficients
            title = 'Relative coefficients of regressors'

        index_translator = self._get_index_translator(coeff_names)
        coefficients = QFSeries(index=pd.Index(coeff_names), data=coeff_values)

        bar_chart = BarChart(orientation=Orientation.Horizontal, index_translator=index_translator,
                             thickness=self._bars_width, align='center')

        bar_chart.add_decorator(DataElementDecorator(coefficients, color=bars_colors))
        bar_chart.add_decorator(TitleDecorator(title))
        bar_chart.add_decorator(AxesLabelDecorator(x_label="sensitivity"))

        labels = ['{:.2f}'.format(value) for value in coeff_values]
        self._add_labels_for_bars(bar_chart, coefficients, labels)

        return bar_chart

    def performance_attribution_chart(self) -> BarChart:
        colors_palette = Chart.get_axes_colors()

        unexplained_ret = self.model.unexplained_performance_attribution_ret
        factors_ret = self.model.factors_performance_attribution_ret
        fund_ret = self.model.fund_tms_analysis.cagr

        unexplained_name = "Unexplained"
        factors_names = [self._get_security_name(ticker) for ticker in self.model.coefficients.index.values]

        fund_name = self._get_security_name(self.model.input_data.analysed_tms.name)

        all_values = [unexplained_ret] + list(factors_ret) + [fund_ret]
        all_names = [unexplained_name] + list(factors_names) + [fund_name]
        all_returns = SimpleReturnsSeries(data=all_values, index=pd.Index(all_names))

        colors = [colors_palette[0]] + [colors_palette[1]] * len(factors_names) + [colors_palette[2]]

        index_translator = self._get_index_translator(labels=all_names)
        bar_chart = BarChart(orientation=Orientation.Horizontal, index_translator=index_translator,
                             thickness=self._bars_width, align='center')
        bar_chart.add_decorator(DataElementDecorator(all_returns, color=colors))
        bar_chart.add_decorator(TitleDecorator("Attribution of Fund Annualised Return"))
        bar_chart.add_decorator(AxesLabelDecorator(x_label="annualised return [%]"))
        bar_chart.add_decorator(AxesFormatterDecorator(x_major=PercentageFormatter()))

        labels = ('{:.2f}'.format(value * 100) for value in all_returns)
        self._add_labels_for_bars(bar_chart, all_returns, labels)

        return bar_chart

    def risk_contribution_chart(self) -> BarChart:
        colors_palette = Chart.get_axes_colors()

        tickers = self.model.input_data.regressors_df.columns.values
        names = [self._get_security_name(ticker) for ticker in tickers]
        risk_contributions = QFSeries(data=self.model.risk_contribution.values, index=pd.Index(names))

        index_translator = self._get_index_translator(labels=names)
        bar_chart = BarChart(orientation=Orientation.Horizontal, index_translator=index_translator,
                             thickness=self._bars_width, align='center')
        bar_chart.add_decorator(DataElementDecorator(risk_contributions, color=colors_palette[1]))
        bar_chart.add_decorator(TitleDecorator("Risk contribution"))
        bar_chart.add_decorator(AxesLabelDecorator(x_label="risk contribution [%]"))
        bar_chart.add_decorator(AxesFormatterDecorator(x_major=PercentageFormatter()))
        labels = ('{:.2f}'.format(value * 100) for value in risk_contributions)
        self._add_labels_for_bars(bar_chart, risk_contributions, labels, margin=0.001)

        return bar_chart

    def correlation_matrix_chart(self) -> HeatMapChart:
        data = self.model.correlation_matrix
        names = [self._get_security_name(ticker) for ticker in self.model.correlation_matrix.columns.values]
        heatmap_chart = HeatMapChart(data, min_value=-1, max_value=1)

        heatmap_chart.add_decorator(AxisTickLabelsDecorator(axis=Axis.X, labels=names))
        heatmap_chart.add_decorator(AxisTickLabelsDecorator(axis=Axis.Y, labels=reversed(names)))
        heatmap_chart.add_decorator(ValuesAnnotations())
        heatmap_chart.add_decorator(ColorBar())
        heatmap_chart.add_decorator(TitleDecorator("Correlation matrix"))

        return heatmap_chart

    def get_r_squared_info(self) -> str:
        r_squared_fit = self.model.r_squared

        # name of the fit should take 35 characters and be right aligned
        header = '        R-Square     Name'
        equals_separator = '============================================================='
        fit_info = '        {r_square:<8.6f}     {fit_name:<35.35s}'.format(r_square=r_squared_fit, fit_name='Fit')
        dash_separator = '-------------------------------------------------------------'

        r_squared_of_predictors = self.model.r_squared_of_each_predictor
        predictors_info = []
        for ticker, r_squared in r_squared_of_predictors.iteritems():
            info = '        {r_squared:<8.6f}     {predictor_name:<35.35s}'.format(
                r_squared=r_squared, predictor_name=self._get_security_name(ticker))
            predictors_info.append(info)

        return '\n'.join([header, equals_separator, fit_info, dash_separator] + predictors_info) + '\n'

    def get_durbin_watson_test_info(self) -> str:
        return 'Durbin-Watson test: \n        d = {:1.3f}'.format(self.model.durbin_watson_test)

    def get_autocorrelation_info(self) -> str:
        auto_correlations = self.model.autocorrelation
        infos = ['autocorrelations:']

        for i, auto_corr in enumerate(auto_correlations, start=1):
            infos.append('        Autocorrelation (lag {:d}): {:s}'.format(i, str(auto_corr)))

        return '\n'.join(infos)

    def get_t_statistics_info(self) -> str:
        t_values = self.model.t_values
        if self.model.input_data.is_fit_intercept:
            t_values = t_values[:-1]  # don't take the last t-value which corresponds to the "constant" factor

        infos = ["t-statistics:"]
        for ticker, t_val in t_values.iteritems():
            infos.append('        {:< 9.3f}   {:s}'.format(t_val, self._get_security_name(ticker)))

        return '\n'.join(infos)

    def get_p_values_info(self) -> str:
        p_values = self.model.p_values
        if self.model.input_data.is_fit_intercept:
            p_values = p_values[:-1]  # don't take the last t-value which corresponds to the "constant" factor

        infos = ["p-values"]
        for ticker, p_val in p_values.iteritems():
            infos.append('        {:< 9.3f}   {:s}'.format(p_val, self._get_security_name(ticker)))

        return '\n'.join(infos)

    def get_condition_number_info(self) -> str:
        cond_number = self.model.condition_number
        return '        ContidionIndex = {:5.2f}'.format(cond_number)

    def cooks_distance_chart(self) -> LineChart:
        cooks_dist = self.model.cooks_distance_tms
        chart = LineChart()

        colors = cycle(Chart.get_axes_colors())
        color = next(colors)

        marker_props = {'alpha': 0.7}
        stemline_props = {'linestyle': '-.', 'linewidth': 0.2}
        baseline_props = {'visible': False}
        marker_props['markeredgecolor'] = color
        marker_props['markerfacecolor'] = color
        stemline_props['color'] = color

        data_elem = StemDecorator(cooks_dist, marker_props=marker_props,
                                  stemline_props=stemline_props, baseline_props=baseline_props)

        chart.add_decorator(data_elem)
        chart.add_decorator(TitleDecorator("Cook's Distance"))
        chart.add_decorator(AxesLabelDecorator(y_label="max change of coefficients"))

        return chart

    def regressors_and_explained_variable_chart(self) -> LineChart:
        regressors_df = self.model.input_data.regressors_df
        fund_tms = self.model.input_data.analysed_tms

        chart = LineChart()
        legend = LegendDecorator()

        # add data to the chart and the legend
        marker_props_template = {'alpha': 0.5}
        stemline_props_template = {'linestyle': '-.', 'linewidth': 0.2}
        baseline_props = {'visible': False}

        regressors_and_fund_df = pd.concat([regressors_df, fund_tms], axis=1)
        colors = cycle(Chart.get_axes_colors())

        for ticker, series in regressors_and_fund_df.iteritems():
            marker_props = marker_props_template.copy()
            stemline_props = stemline_props_template.copy()

            color = next(colors)
            marker_props['markeredgecolor'] = color
            marker_props['markerfacecolor'] = color
            stemline_props['color'] = color
            data_elem = StemDecorator(series, marker_props=marker_props, stemline_props=stemline_props,
                                      baseline_props=baseline_props)
            chart.add_decorator(data_elem)
            legend.add_entry(data_elem, self._get_security_name(ticker))

        # add decorators to the chart
        chart.add_decorator(TitleDecorator("Returns"))
        chart.add_decorator(AxesLabelDecorator(y_label="return [%]"))
        chart.add_decorator(legend)
        chart.add_decorator(AxesFormatterDecorator(y_major=PercentageFormatter()))

        return chart

    def enet_coeffs_chart(self):
        if self._enet_factors_identifier is None:
            return None

        return self._enet_factors_identifier.coeffs_chart

    def enet_mse_chart(self):
        if self._enet_factors_identifier is None:
            return None

        return self._enet_factors_identifier.mse_chart

    def _get_index_translator(self, labels):
        tick_locations = range(len(labels))
        labels_to_locations_dict = dict(zip(labels, tick_locations))
        return IndexTranslator(labels_to_locations_dict)

    def _add_labels_for_bars(self, bar_chart, values_series, labels, margin=0.002):
        index_translator = bar_chart.index_translator
        x_positions = values_series.apply(lambda x: max(0, x)).values + margin
        y_positions = index_translator.translate(values_series.index.values)

        for x_pos, y_pos, label in zip(x_positions, y_positions, labels):
            text_decorator = TextDecorator(label, y=DataCoordinate(y_pos), x=DataCoordinate(x_pos), clip_on=False,
                                           verticalalignment='center', horizontalalignment='left')
            bar_chart.add_decorator(text_decorator)

    def _get_security_name(self, ticker):
        if not isinstance(ticker, str):
            ticker = ticker.as_string()

        return self.ticker_to_security_name_dict.get(ticker, ticker)
