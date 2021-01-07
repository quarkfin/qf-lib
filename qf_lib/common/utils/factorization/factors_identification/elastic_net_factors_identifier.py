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

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import ElasticNetCV

from qf_lib.common.utils.factorization.factors_identification.factors_identifier import FactorsIdentifier
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


class ElasticNetFactorsIdentifier(FactorsIdentifier):
    """
    Class used for identifying factors in the model with Elastic Net method (with Cross-validation).

    Parameters
    ----------
    max_number_of_regressors
        maximal number of regressors that can be included in the model
    epsilon
         if abs(coefficient) is smaller than epsilon it is considered to be zero, thus won't be included
         in the model
    l1_ratio
        value between [0,1] the higher the simpler and more sensitive model is to collinear factors
    number_of_alphas
        number of different lambda values tested
    is_intercept
        True if intercept should be included in the model, False otherwise
    graphic_debug
        default False; If True, then some additional debug info will be plotted (used when tuning
        the ElasticNetFactorsIdentifier's parameters)

    """

    NUMBER_OF_FOLDS = 10
    """ number of folds in the k-fold cross-validation. """

    MIN_NUM_OF_1SE_REGRESSORS = 2
    """
    minimal number of regressors taken for the alpha_1se (max. alpha for which the MSE is within 1 std.
    from the min. MSE). If number of regressors is smaller, then coefficients for min. MSE are taken.
    """

    def __init__(self, max_number_of_regressors: int = 10, epsilon: float = 0.05, l1_ratio: float = 1,
                 number_of_alphas: int = 75, is_intercept: bool = True, graphic_debug: bool = False):
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.max_number_of_regressors = max_number_of_regressors
        self.epsilon = epsilon
        self.l1_ratio = l1_ratio
        self.number_of_alphas = number_of_alphas
        self.is_intercept = is_intercept
        self.graphic_debug = graphic_debug
        self.coeffs_chart = None
        self.mse_chart = None

    def select_best_factors(self, regressors_df: QFDataFrame, analysed_tms: QFSeries) -> QFDataFrame:
        """
        Returns the dataframe which is the subset of the original regressors_df but only contains rows for dates
        common for it and analysed_tms and only contains columns for coefficients which should be included in the model.
        Factors are identified using Elastic Net method with Cross-Validation (for calculating the MSE).

        Parameters
        ----------
        regressors_df
            dataframe containing data for regressors (e.g. daily log-returns)
        analysed_tms
            timeseries of analysed data (data which should be modeled with regressors, e.g. daily log-returns)

        Returns
        -------
        QFDataFrame
            Subset of the original regressors_df. Only contains rows corresponding to dates common for it and
            analysed_tms. Only contains columns corresponding to coefficients which should be included in the model
        """
        self.logger.debug("Model selection using Elastic Net in progress...")

        alphas, index_1se, enet_optimizer = self._optimize_using_enet(analysed_tms, regressors_df)

        # vector of vectors of coefficients
        coeffs_path = self._get_coeffs_path(alphas, analysed_tms, regressors_df)

        # by default take the solution for 1SE from the best fit
        coefficients_vector = coeffs_path[index_1se]
        mean_square_errors = np.mean(enet_optimizer.mse_path_, axis=1)

        solutions_idx = index_1se
        index_min_se = np.argmin(mean_square_errors)  # type: int

        num_of_nonzero_coeffs = self._number_of_non_zero_coefficients(coefficients_vector)
        if num_of_nonzero_coeffs <= self.MIN_NUM_OF_1SE_REGRESSORS:
            solutions_idx = index_min_se
            coefficients_vector = coeffs_path[solutions_idx]

        if self._number_of_non_zero_coefficients(coefficients_vector) <= self.max_number_of_regressors:
            self.logger.info("Solution within one std from minimum MSE found")
        else:
            self.logger.warning('No solution within one std from minimum MSE')
            coefficients_vector, solutions_idx = self._simplify_model(coeffs_path, index_1se)

        included_coefficients_idx = self._indices_of_non_zero_coefficients(coefficients_vector)
        selected_regressors_df = regressors_df.iloc[:, np.sort(included_coefficients_idx)]

        if self.graphic_debug:
            self.coeffs_chart, self.mse_chart = self._plot_graphic_debug_info(
                alphas, coeffs_path, mean_square_errors, solutions_idx, index_min_se)

        return selected_regressors_df

    def _simplify_model(self, coeffs_path, index_1se):
        # find fit with fewer regressors than MAX_NUMBER_OF_REGRESSORS
        solutions_idx = index_1se - 1
        coefficients_vector = coeffs_path[solutions_idx]
        while self._number_of_non_zero_coefficients(coefficients_vector) > self.max_number_of_regressors \
                and solutions_idx != 0:
            solutions_idx -= 1
            coefficients_vector = coeffs_path[solutions_idx]
        return coefficients_vector, solutions_idx

    def _optimize_using_enet(self, analysed_tms, regressors_df):
        enet_optimizer = ElasticNetCV(l1_ratio=self.l1_ratio, n_alphas=self.number_of_alphas,
                                      cv=self.NUMBER_OF_FOLDS, fit_intercept=self.is_intercept)
        enet_optimizer.fit(regressors_df, analysed_tms)
        self.logger.debug('Finished Elastic Net analysis')
        alphas = enet_optimizer.alphas_
        mean_square_errors = np.mean(enet_optimizer.mse_path_, axis=1)
        index_1se = self._get_arg_alpha_1se(alphas, mean_square_errors)

        return alphas, index_1se, enet_optimizer

    def _plot_graphic_debug_info(self, alphas, coeffs_path, mean_square_errors, solutions_idx, index_min_se):
        min_se_solution = alphas[index_min_se]  # alpha for a solution with minimal mean error
        chosen_solution = alphas[solutions_idx]  # alpha for chosen solution

        # Elastic Net (using Cross Validation)
        coeffs_chart = self._create_coeffs_debug_chart(alphas, chosen_solution, coeffs_path, min_se_solution)

        # Cross-validated avg. MSE of Elastic Net fit
        mse_chart = self._create_mse_debug_chart(alphas, chosen_solution, mean_square_errors, min_se_solution)

        return coeffs_chart, mse_chart

    def _create_coeffs_debug_chart(self, alphas, chosen_solution, coeffs_path, min_se_solution):
        coeffs_chart = LineChart()
        coefficients_paths = QFDataFrame(data=coeffs_path, index=pd.Index(alphas))
        for _, path in coefficients_paths.iteritems():
            coeffs_chart.add_decorator(DataElementDecorator(path))
        coeffs_chart.add_decorator(TitleDecorator("Elastic Net (using Cross Validation)"))
        coeffs_chart.add_decorator(VerticalLineDecorator(x=min_se_solution, linestyle='-.'))
        coeffs_chart.add_decorator(VerticalLineDecorator(x=chosen_solution, linestyle='-'))
        coeffs_chart.plot()
        coeffs_chart.axes.invert_xaxis()

        return coeffs_chart

    def _create_mse_debug_chart(self, alphas, chosen_solution, mean_square_errors, min_se_solution):
        mse_chart = LineChart()
        mean_square_errors_paths = QFDataFrame(data=mean_square_errors, index=pd.Index(alphas))
        mse_chart.add_decorator(TitleDecorator("Cross-validated avg. MSE of Elastic Net fit"))
        for _, path in mean_square_errors_paths.iteritems():
            mse_chart.add_decorator(DataElementDecorator(path))
        mse_chart.add_decorator(VerticalLineDecorator(x=min_se_solution, linestyle='-.'))
        mse_chart.add_decorator(VerticalLineDecorator(x=chosen_solution, linestyle='-'))
        mse_chart.plot()
        mse_chart.axes.invert_xaxis()

        return mse_chart

    def _get_coeffs_path(self, alphas, common_analysed_tms, common_regressors_df):
        coeffs_path = []
        for alpha in alphas:
            model = ElasticNet(alpha=alpha, l1_ratio=self.l1_ratio)
            model.fit(common_regressors_df, common_analysed_tms)
            coeffs_path.append(model.coef_)

        return coeffs_path

    def _get_arg_alpha_1se(self, alphas, mean_square_errors):
        mse_std = np.std(mean_square_errors)
        min_mse = np.min(mean_square_errors)

        max_mse_limit = min_mse + mse_std

        # find largest alpha lower then the given limit
        alphas_within_the_limit = alphas[mean_square_errors < max_mse_limit]
        alpha_1se = np.max(alphas_within_the_limit)

        # np.argmax finds the index of first True occurrence in bool array (in this case)
        index_of_alpha_1se = np.argmax(alphas == alpha_1se)  # type: int
        return index_of_alpha_1se

    def _number_of_non_zero_coefficients(self, coefficients_vector):
        coefficients_greater_than_epsilon = np.abs(coefficients_vector) > self.epsilon  # type: np.ndarray
        return np.sum(coefficients_greater_than_epsilon)

    def _indices_of_non_zero_coefficients(self, coefficients_vector):
        coefficients_greater_than_epsilon = np.abs(coefficients_vector) > self.epsilon  # type: np.ndarray
        return np.flatnonzero(coefficients_greater_than_epsilon)  # gives the indices of all True values
