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

from math import floor

import numpy as np
import pandas as pd
import statsmodels.api as sm
from numpy.linalg import inv, cond
from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.stats.stattools import durbin_watson

from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.timeseries_analysis.return_attribution_analysis import ReturnAttributionAnalysis
from qf_lib.common.timeseries_analysis.risk_contribution_analysis import RiskContributionAnalysis
from qf_lib.common.utils.factorization.data_models.data_model_input import DataModelInput
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries


class DataModel:
    """
    Class grouping the results of factorization.

    Parameters
    ----------
    data_model_input
        data from which the model is built
    """

    AUTOCORR_MAX_LAG = 3
    """
    int
    maximal lag used during testing for autocorrelation of the fit; lags used for testing will be values
    1, ..., autocorr_max_lag
    """

    AUTOCORR_SIGNIFICANCE_LEVEL = 0.05
    """
    float
    significance level for the autocorrelation of the fit test
    """

    def __init__(self, data_model_input: DataModelInput):
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.input_data = data_model_input

        ########################################################
        # OUTPUT VARIABLES                                     #
        ########################################################

        self.fit_model = None
        """
        Structure with a result of multilinear regression (based on all data points and using OLS to calculate
        coefficients).
        """

        self.fitted_tms = None
        """ Fitted (predicted) response values based on input data. """

        self.intercept = 0.0
        """ Constant alpha (y = beta * x + constant). """

        self.coefficients = None
        """ Vector of coefficients [beta1, beta2, ...]. """

        self.fit_tms_analysis = None
        """ TimeseriesAnalysis class based on returns of the fit. """

        self.fund_tms_analysis = None
        """ TimeseriesAnalysis class based on returns of the analysed fund. """

        self.risk_contribution = None
        """ Vector containing normalised risk contribution of each factor. """

        self.factors_performance_attribution_ret = None
        """ Vector containing annualised performance attribution of each factor. """

        self.unexplained_performance_attribution_ret = None
        """ Scalar with annualised return unexplained by factors. """

        self.durbin_watson_test = None
        """
        Used to test if linear regression residuals are uncorrelated. Small p-values indicate correlation among
        residuals.
        """

        self.autocorrelation = None
        """ Extension of Durbin-Watson test to add many lags (1-5).  0 - not autocorrelated, 1 - autocorrelated. """

        self.heteroskedasticity = None
        """ Probability of a hypothesis that the error variance doesn't depend on input data (regressors). """

        self.correlation_matrix = None

        self.condition_number = None
        """
        Condition number of a matrix measures the sensitivity of the solution of a system of linear equations
        to errors in the data.
        """

        self.r_squared_of_each_predictor = None
        """ Concerns about collinearity can be ignored if rSquare is higher than rSquare of each predictor. """

        self.in_sample_and_out_sample_returns = None
        """
        Returns of a fit based on in-sample coefficients. Vector with in-sample and out-of-sample simple returns.
        Its length is equal to length of fitted returns.
        """

        self.oos_start_date = None
        """ Date on which the Out-Of-Sample period started (In-Sample vs Out-Of-Sample test). """

        self.cooks_distance_tms = None
        """ Cooks distance. Used for checking the influence of outliers for the model. """

        self.ols_influence = None
        """ Class for calculating outliers and influence measures for OLS result. """

    def setup(self):
        self._calc_coefficients()
        self._setup_return_analysis_of_fund_and_fit(self.fitted_tms)
        self._setup_out_of_sample_fit()

        residuals = self.fit_model.resid
        self.durbin_watson_test = durbin_watson(residuals)

        regressors_df = self.input_data.regressors_df
        analysed_tms = self.input_data.analysed_tms
        self.risk_contribution = RiskContributionAnalysis.get_risk_contribution(
            regressors_df, self.coefficients, analysed_tms)

        factors_perf_attrib, unexplained_perf_attrib = ReturnAttributionAnalysis.get_factor_return_attribution(
            analysed_tms, self.fitted_tms, regressors_df, self.coefficients, self.intercept)
        self.factors_performance_attribution_ret = factors_perf_attrib
        self.unexplained_performance_attribution_ret = unexplained_perf_attrib

        self._setup_correlations(self.fitted_tms)
        self.condition_number = cond(regressors_df.values)
        self._setup_r_square_of_each_predictor()
        self._setup_autocorrelation(residuals)
        _, _, _, self.heteroskedasticity = het_breuschpagan(residuals, self.fit_model.model.exog)
        self._setup_cooks_distance(self.fit_model)

    @property
    def r_squared(self) -> float:
        return self.fit_model.rsquared_adj

    @property
    def t_values(self) -> QFSeries:
        return self.fit_model.tvalues

    @property
    def p_values(self) -> QFSeries:
        return self.fit_model.pvalues

    def _calc_coefficients(self):
        regressors = self.input_data.regressors_df
        if self.input_data.is_fit_intercept:
            regressors = sm.add_constant(regressors, prepend=False)

        analysed_tms = self.input_data.analysed_tms
        model = sm.OLS(analysed_tms, regressors)
        fit = model.fit()

        self.logger.info("Fitted model for given regressors and fund returns time series:")
        self.logger.info(fit.summary())

        coefficients_, intercept_ = self._get_model_params(fit)

        self.coefficients = coefficients_
        self.intercept = intercept_
        series_type = type(analysed_tms)
        self.fitted_tms = series_type(data=fit.fittedvalues, index=analysed_tms.index.copy(),
                                      name="Fitted returns")
        self.fit_model = fit

    def _get_model_params(self, fit):
        if self.input_data.is_fit_intercept:
            coefficients_ = fit.params[:-1]  # last value is a constant parameter
            intercept_ = fit.params[-1]  # it needs to be extracted into intercept_ attribute
        else:
            coefficients_ = fit.params
            intercept_ = 0.0

        return coefficients_, intercept_

    def _setup_return_analysis_of_fund_and_fit(self, fitted_tms):
        freq = self.input_data.frequency
        analysed_tms = self.input_data.analysed_tms
        self.fit_tms_analysis = TimeseriesAnalysis(fitted_tms, freq)
        self.fund_tms_analysis = TimeseriesAnalysis(analysed_tms, freq)

    def _setup_out_of_sample_fit(self):
        """
        Creates a fit base just on 2/3 of returns.
        """
        analysed_tms = self.input_data.analysed_tms
        regressors_df = self.input_data.regressors_df
        number_of_data_in_sample = int(floor(len(analysed_tms) * 2 / 3))

        self.oos_start_date = analysed_tms.index[number_of_data_in_sample - 1]

        regressors_in_sample_df = regressors_df.iloc[:number_of_data_in_sample, :]
        fund_returns_in_sample_tms = analysed_tms.iloc[:number_of_data_in_sample]

        if len(regressors_in_sample_df.columns) <= 1:
            return

        self.logger.info("Fitting in sample using {:d} data points".format(number_of_data_in_sample))

        if self.input_data.is_fit_intercept:
            regressors_in_sample_df = sm.add_constant(regressors_in_sample_df, prepend=False)

        model = sm.OLS(fund_returns_in_sample_tms, regressors_in_sample_df)
        fit = model.fit()
        self.logger.info(fit.summary())

        coeffs_in_sample, intercept_in_sample = self._get_model_params(fit)

        portfolio_returns = self._get_weighted_portfolio_rets(
            returns=regressors_df, weights=coeffs_in_sample, intercept=intercept_in_sample)
        self.in_sample_and_out_sample_returns = portfolio_returns

    def _get_weighted_portfolio_rets(self, returns, weights, intercept):
        assert len(returns.columns) == len(weights)

        # normalize weights, so that they contain intercept factor in the end and that they all sum up to 1
        norm_weights = list(weights) + [intercept]
        norm_weights = np.array(norm_weights)
        norm_weights = norm_weights / sum(norm_weights)

        norm_returns = sm.add_constant(returns, prepend=False)

        portfolio_returns = norm_returns.dot(norm_weights)
        portfolio_returns = cast_series(portfolio_returns, type(returns))
        portfolio_returns.__finalize__(returns)

        return portfolio_returns

    def _setup_correlations(self, fitted_tms):
        analysed_tms = self.input_data.analysed_tms
        regressors_df = self.input_data.regressors_df
        data_for_correlation = pd.concat((fitted_tms, regressors_df, analysed_tms), axis=1)
        self.correlation_matrix = cast_dataframe(data_for_correlation.corr(), output_type=QFDataFrame)

    def _setup_r_square_of_each_predictor(self):
        regressors_df = self.input_data.regressors_df
        corr_matrix = regressors_df.corr()
        corr_matrix = cast_dataframe(corr_matrix, output_type=QFDataFrame)
        vif = np.diagonal(inv(corr_matrix))
        r_squared_values = 1 - (1 / vif)
        self.r_squared_of_each_predictor = QFSeries(data=r_squared_values, index=regressors_df.columns.copy())

    def _setup_autocorrelation(self, residuals):
        lags = range(1, self.AUTOCORR_MAX_LAG + 1)

        # p_value is a probability of no autocorrelation present (separate value for each lag)
        return_df = acorr_ljungbox(residuals, lags=lags, return_df=True)  # type: pd.DataFrame
        p_value = return_df["lb_pvalue"]

        self.autocorrelation = p_value <= self.AUTOCORR_SIGNIFICANCE_LEVEL

    def _setup_cooks_distance(self, ols_results):
        ols_influence = OLSInfluence(ols_results)
        cooks_distance, _ = ols_influence.cooks_distance
        dates_index = self.input_data.regressors_df.index
        self.cooks_distance_tms = QFSeries(data=cooks_distance, index=dates_index.copy())
        self.ols_influence = ols_influence
