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

from qf_lib.common.utils.factorization.data_models.data_model import DataModel
from qf_lib.common.utils.factorization.data_models.data_model_input import DataModelInput
from qf_lib.common.utils.factorization.data_models.rolling_window_estimation import RollingWindowsEstimator
from qf_lib.containers.series.qf_series import QFSeries


class RollingDataModel:
    """
    Class for preparing multiple data models using the rolling window.

    Parameters
    ----------
    data_model_input
        data from which the model is built
    """

    def __init__(self, data_model_input: DataModelInput):
        self.input_data = data_model_input

        self.window_size_ = None
        self.step_ = None

        self.coefficients_df = None
        """ Rolling coefficients (factors in columns, different time windows in rows). """

        self.t_stats_df = None
        """ Rolling t-statistics (factors in columns, different time windows in rows). """

        self.p_values_df = None
        """ Rolling p-values (factors in columns, different time windows in rows). """

        self.r_squared_tms = None
        """ Rolling adjusted r squared (different time windows in rows). """

        self.correlations_df = None
        """
        Rolling correlations of different factors with analysed timeseries (factors in columns, different time windows
        in rows).
        """

        self.risk_contribs_df = None
        """ Rolling risk contributions (factors in columns, different time windows in rows). """

        self.factors_performance_attributions_df = None
        """ Rolling performance attributions (factors in columns, different time windows in rows). """

        self.unexplained_performance_attributions_tms = None
        """ Rolling unexplained return attribution (different time windows in rows). """

    def setup(self, window_size=None, step=None):
        """
        Returns the series of models (each model is placed under the date corresponding to the end of its time window).

        Parameters
        ----------
        window_size: int, optional
            number of samples contained in each window. If it's not provided, than it will be calculated automatically
        step: int, optional
            number of samples by which window shall be moved each time it is moved. If the value isn't provided,
            than it will be calculated automatically
        """
        if window_size is None:
            window_size = RollingWindowsEstimator.estimate_rolling_window_size(self.input_data.analysed_tms)
        if step is None:
            step = RollingWindowsEstimator.estimate_rolling_window_step(self.input_data.analysed_tms)

        assert step > 0

        self.window_size_ = window_size
        self.step_ = step

        end_of_window_idx = len(self.input_data.analysed_tms) - 1
        beginning_of_window_idx = end_of_window_idx - window_size

        ref_dates = []
        models = []

        while beginning_of_window_idx >= 0:
            data_model, ref_date = self._get_model_for_window(beginning_of_window_idx, end_of_window_idx)
            models.append(data_model)
            ref_dates.append(ref_date)

            end_of_window_idx -= step
            beginning_of_window_idx -= step

        models_series_ = QFSeries(data=models, index=ref_dates)

        self.coefficients_df = models_series_.apply(lambda model: model.coefficients)
        self.t_stats_df = models_series_.apply(lambda model: model.t_values)
        self.p_values_df = models_series_.apply(lambda model: model.p_values)
        self.r_squared_tms = models_series_.apply(lambda model: model.r_squared)
        self.risk_contribs_df = models_series_.apply(lambda model: model.risk_contribution)

        self.factors_performance_attributions_df = models_series_.apply(
            lambda model: model.factors_performance_attribution_ret)
        self.unexplained_performance_attributions_tms = models_series_.apply(
            lambda model: model.unexplained_performance_attribution_ret)

        # select correlations of different series with analysed timeseries
        self.correlations_df = models_series_.apply(lambda model: model.correlation_matrix.iloc[-1, :-1])

    def _get_model_for_window(self, beginning_of_window_idx, end_of_window_idx):
        frequency = self.input_data.frequency
        is_fit_intercept = self.input_data.is_fit_intercept

        ref_date = self.input_data.analysed_tms.index[end_of_window_idx]

        regressors_df = self.input_data.regressors_df.iloc[beginning_of_window_idx:end_of_window_idx + 1, :]
        fund_tms = self.input_data.analysed_tms.iloc[beginning_of_window_idx:end_of_window_idx + 1]

        input_data = DataModelInput(regressors_df, fund_tms, frequency, is_fit_intercept)

        data_model = DataModel(input_data)
        data_model.setup()

        return data_model, ref_date
