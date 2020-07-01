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

from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import ElasticNetCV

from qf_lib.common.utils.factorization.factors_identification.factors_identifier import FactorsIdentifier
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class ElasticNetFactorsIdentifierSimplified(FactorsIdentifier):
    """
    Class used for identifying factors in the model with Elastic Net method (with Cross-validation). Implementation
    was simplified so that the stock ElasticNetCV optimizer was used.

    Parameters
    ----------
    epsilon
         if abs(coefficient) is smaller than epsilon it is considered to be zero, thus won't be included
         in the model
    l1_ratio
        value between [0,1] the higher the simpler and more sensitive model is to collinear factors
    number_of_alphas
        number of different lambda values tested
    is_fit_intercept
        True if intercept should be included in the model, False otherwise

    """

    NUMBER_OF_FOLDS = 10
    """ number of folds in the k-fold cross-validation. """

    MIN_NUM_OF_1SE_REGRESSORS = 2
    """
    minimal number of regressors taken for the alpha_1se (max. alpha for which the MSE is within 1 std.
    from the min. MSE). If number of regressors is smaller, then coefficients for min. MSE are taken.
    """

    def __init__(self, epsilon: float = 0.05, l1_ratio: float = 1,
                 number_of_alphas: int = 75, is_fit_intercept: bool = True):
        """        """
        self.epsilon = epsilon
        self.l1_ratio = l1_ratio
        self.number_of_alphas = number_of_alphas
        self.is_intercept = is_fit_intercept

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
        estimator = ElasticNetCV(l1_ratio=self.l1_ratio, n_alphas=self.number_of_alphas, cv=self.NUMBER_OF_FOLDS,
                                 fit_intercept=self.is_intercept)
        feature_selector = SelectFromModel(estimator, threshold=self.epsilon)
        feature_selector.fit(regressors_df, analysed_tms)
        selected_features = feature_selector.get_support()
        selected_regressors_df = regressors_df.loc[:, selected_features]

        return selected_regressors_df
