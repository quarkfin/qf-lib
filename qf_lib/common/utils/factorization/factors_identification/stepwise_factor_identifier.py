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

from typing import List

import numpy as np
from sklearn.linear_model import LinearRegression

from qf_lib.common.utils.factorization.factors_identification.factors_identifier import FactorsIdentifier
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class StepwiseFactorsIdentifier(FactorsIdentifier):
    """
    Class used for identifying factors in the model with Stepwise Regression (with Forward Feature Selection).

    Parameters
    ----------
    epsilon
        minimal improvement of model. If adding next factor doesn't imporve the score by epsilon, then the algorithm
        is stopped and new factor is not added.
    is_intercept
        True if the output model shall include the intercept, False otherwise (e.g. because data is centered
        already).
    """

    def __init__(self, epsilon: float = 0.05, is_intercept: bool = True):
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.epsilon = epsilon
        self.linear_regression = LinearRegression(fit_intercept=is_intercept)

    @property
    def intercept(self) -> bool:
        return self.linear_regression.fit_intercept

    def select_best_factors(self, regressors_df: QFDataFrame, analysed_tms: QFSeries) -> QFDataFrame:
        """
        Returns the dataframe which is the subset of the original regressors_df but only contains rows for dates
        common for it and analysed_tms and only contains columns for coefficients which should be included in the model.
        Factors are identified using Stepwise algorithm.

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
        self.logger.info("Model selection using Stepwise in progress...")

        selected_columns_inds = self._select_with_forward_selection(regressors_df, analysed_tms)
        selected_columns_inds = np.sort(selected_columns_inds)

        self.logger.info("Finished Stepwise regression analysis")

        return regressors_df.iloc[:, selected_columns_inds]

    def _select_with_forward_selection(self, regressors_df, analysed_tms) -> List[str]:
        """
        Used stepwise forward selection algorithm for selecting significant factors for the model.

        Returns
        -------
        List[str]
            indices of columns selected for the model
        """
        total_columns_number = len(regressors_df.columns)
        remaining_columns = list(range(total_columns_number))
        selected_columns_inds = []

        current_score = 0.0
        made_improvement = True

        while made_improvement and remaining_columns:
            new_score, best_candidates_idx = \
                self._get_next_factor(analysed_tms, regressors_df, selected_columns_inds, remaining_columns)

            # check if adding a new factor improves the model at least by self.epsilon
            if new_score - current_score >= self.epsilon:
                remaining_columns.remove(best_candidates_idx)
                selected_columns_inds.append(best_candidates_idx)
                current_score = new_score
            else:
                made_improvement = False

        return selected_columns_inds

    def _get_next_factor(self, analysed_tms, regressors_df, selected_columns_inds, unused_columns_inds):
        scores_of_candidates = []

        for candidate in unused_columns_inds:
            columns_to_pick_inds = [candidate] + selected_columns_inds
            used_regressors = regressors_df.iloc[:, columns_to_pick_inds]
            self.linear_regression.fit(used_regressors, analysed_tms)
            r_squared = self.linear_regression.score(used_regressors, analysed_tms)
            scores_of_candidates.append(r_squared)

        # index of best candidate in the candidates_array
        best_candidate = np.argmax(scores_of_candidates)
        best_candidates_score = scores_of_candidates[best_candidate]

        # index of best candidate in the regressors_df.columns array
        best_candidates_idx = unused_columns_inds[best_candidate]

        return best_candidates_score, best_candidates_idx
