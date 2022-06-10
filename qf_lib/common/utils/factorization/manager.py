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

from typing import Tuple

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.data_cleaner import DataCleaner
from qf_lib.common.utils.dateutils.get_values_common_dates import get_values_for_common_dates
from qf_lib.common.utils.factorization.data_models.data_model import DataModel
from qf_lib.common.utils.factorization.data_models.data_model_input import DataModelInput
from qf_lib.common.utils.factorization.data_models.rolling_data_model import RollingDataModel
from qf_lib.common.utils.factorization.factors_identification.factors_identifier import FactorsIdentifier
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class FactorizationManager:
    """
    Facade class for factorization.

    Parameters
    ----------
    analysed_tms
        must have a set name in order to be displayed properly later on
    regressors_df
        must have a set name for each column in order to be displayed properly later on
    frequency
        frequency of every series (the same for all)
    factors_identifier
        class used for identifying significant factors for the model (picks them up from regressors_df)
    is_fit_intercept
        default True; True if the calculated model should include the intercept coefficient

    """

    def __init__(self, analysed_tms: QFSeries, regressors_df: QFDataFrame, frequency: Frequency,
                 factors_identifier: FactorsIdentifier, is_fit_intercept: bool = True):
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.analysed_tms = analysed_tms.to_simple_returns()
        self.regressors_df = regressors_df.to_simple_returns()

        self.frequency = frequency
        self.factors_identifier = factors_identifier
        self.is_fit_intercept = is_fit_intercept

        self.used_regressors_ = None        # data frame of regressors used in the model
        self.used_fund_returns_ = None      # analysed timeseries without dates unused in the regression
        self.coefficients_vector_ = None    # vector of coefficients for each regressor used in the model
        self.intercept_ = None              # the independent term in a linear model

    def extract_data_for_analysis(self) -> Tuple[QFDataFrame, QFSeries]:
        """
        Extracts data which is useful for building the model explaining the fund's timeseries.

        Returns
        -------
        Tuple[QFDataFrame, QFSeries]
            Dataframe containing only those regressors which are useful for modeling fund's timeseries and a Timeseries
            of fund which is preprocessed (cleaned data)
        """
        common_regressors_df, common_analysed_tms = self._preprocess_data(self.analysed_tms, self.regressors_df)
        selected_regressors_df = \
            self.factors_identifier.select_best_factors(common_regressors_df, common_analysed_tms)

        self.used_regressors_ = selected_regressors_df
        self.used_fund_returns_ = common_analysed_tms

        return selected_regressors_df, common_analysed_tms

    def get_factorization_data_model(self) -> DataModel:
        """
        Creates model explaining fund's timeseries.
        """
        model_input = DataModelInput(self.used_regressors_, self.used_fund_returns_, self.frequency,
                                     self.is_fit_intercept)
        data_model = DataModel(model_input)
        data_model.setup()
        return data_model

    def get_rolling_factorization_data_model(self) -> RollingDataModel:
        """
        Creates multiple models explaining fund's timeseries (one model for each time window).
        """
        model_input = DataModelInput(self.used_regressors_, self.used_fund_returns_, self.frequency,
                                     self.is_fit_intercept)

        data_model = RollingDataModel(model_input)
        data_model.setup()
        return data_model

    def _preprocess_data(self, analysed_tms, regressors_df):
        """
        Cleans the data before they are processed (e.g. removes regressors containing too many missing data,
        proxies missing data).
        """

        self.logger.debug("Length of input timeseries: {:d} \n".format(len(analysed_tms)))

        data_cleaner = DataCleaner(regressors_df)
        common_regressors_df = data_cleaner.proxy_using_regression(analysed_tms, columns_type=SimpleReturnsSeries)
        common_regressors_df, common_analysed_tms = get_values_for_common_dates(common_regressors_df, analysed_tms)

        self.logger.debug("Length of preprocessed timeseries: {:d}".format(common_analysed_tms.size))
        self.logger.debug("Number of regressors: {:d}".format(common_regressors_df.shape[1]))

        return common_regressors_df, common_analysed_tms
