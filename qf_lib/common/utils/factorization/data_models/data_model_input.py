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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class DataModelInput:
    """ Class storing an input data from which FactorizationDataModel is built.
    Parameters
    ----------
    regressors_df
        dataframe of regressors which should be included in the final model
    analysed_tms
        timeseries of returns which should be modeled using regressors
    frequency
        frequency of data used in both regressors and analysed timeseries
    is_fit_intercept
        True if the model should contain the intercept; False otherwise
    """

    def __init__(self, regressors_df: SimpleReturnsDataFrame, analysed_tms: SimpleReturnsSeries, frequency: Frequency,
                 is_fit_intercept: bool):
        assert len(regressors_df.index) == len(analysed_tms)

        self.regressors_df = regressors_df
        self.analysed_tms = analysed_tms
        self.is_fit_intercept = is_fit_intercept
        self.frequency = frequency
