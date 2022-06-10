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

import pandas as pd
from matplotlib.dates import DateFormatter

from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.factorization.data_models.rolling_data_model import RollingDataModel
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


class RollingDataPresenter:
    """
    Class used for presenting the data stored in the RollingFactorizationDataModel.
    """

    def __init__(self, rolling_model: RollingDataModel):
        self.rolling_model = rolling_model

    def general_info(self) -> str:
        return 'Values are calculated based on {window_size:d} data samples rolling \n' \
               'with {num_of_samples:d} sample(s) shift. \n' \
               'Frequency of the data points is {frequency:s}. \n'.format(
                   window_size=self.rolling_model.window_size_,
                   num_of_samples=self.rolling_model.step_,
                   frequency=str(self.rolling_model.input_data.frequency)
               )

    def regression_coefficients_chart(self) -> LineChart:
        rolling_coeffs = self.rolling_model.coefficients_df
        line_chart = self._create_line_chart(rolling_values=rolling_coeffs, title='Rolling regression coefficients')
        return line_chart

    def t_statistics_chart(self) -> LineChart:
        rolling_t_stats = self.rolling_model.t_stats_df
        line_chart = self._create_line_chart(rolling_values=rolling_t_stats, title='Rolling t-statistics')
        return line_chart

    def p_values_chart(self) -> LineChart:
        rolling_p_values = self.rolling_model.p_values_df
        line_chart = self._create_line_chart(rolling_values=rolling_p_values, title='Rolling p-Value')
        return line_chart

    def r_squared_chart(self) -> LineChart:
        rolling_r_squared = self.rolling_model.r_squared_tms
        rolling_r_squared = rolling_r_squared.to_frame(name='R Squared Adjusted')
        line_chart = self._create_line_chart(rolling_values=rolling_r_squared, title='R Squared')
        return line_chart

    def correlations_chart(self) -> LineChart:
        # select correlations of different series with analysed timeseries
        rolling_correlations = self.rolling_model.correlations_df
        line_chart = self._create_line_chart(rolling_values=rolling_correlations, title='Correlation')
        return line_chart

    def risk_contribution_chart(self) -> LineChart:
        rolling_risk_contribs = self.rolling_model.risk_contribs_df
        line_chart = self._create_line_chart(rolling_values=rolling_risk_contribs, title='Risk Contribution')
        return line_chart

    def performance_attribution_chart(self) -> LineChart:
        rolling_factors_performance_attributions = self.rolling_model.factors_performance_attributions_df
        rolling_unexplained_perf_attribs = self.rolling_model.unexplained_performance_attributions_tms
        rolling_unexplained_perf_attribs.name = 'Unexplained/Alpha'
        rolling_perf_attribs = pd.concat([rolling_factors_performance_attributions, rolling_unexplained_perf_attribs],
                                         axis=1)
        line_chart = self._create_line_chart(rolling_values=rolling_perf_attribs, title='Performance Attribution')
        return line_chart

    def _create_line_chart(self, rolling_values, title):
        line_chart = LineChart()
        legend = LegendDecorator()

        for column_name, values_tms in rolling_values.iteritems():
            coeff_tms_data_elem = DataElementDecorator(values_tms)
            line_chart.add_decorator(coeff_tms_data_elem)
            legend.add_entry(coeff_tms_data_elem, column_name)

        full_title_str = "".join([title, ' {:d} samples rolling'.format(self.rolling_model.window_size_)])
        line_chart.add_decorator(TitleDecorator(full_title_str))
        line_chart.add_decorator(AxesFormatterDecorator(x_major=DateFormatter(fmt=str(DateFormat.YEAR_DOT_MONTH))))
        line_chart.add_decorator(legend)

        return line_chart
