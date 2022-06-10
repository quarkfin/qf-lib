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

import datetime
from typing import Tuple

import numpy as np
import pandas as pd

from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.sample_column_names import generate_sample_column_names


def get_analysed_tms_and_regressors(dates_span: int = 1000, num_of_regressors: int = 7,
                                    start_date: datetime.datetime = str_to_date('2016-01-01'),
                                    mean_return: float = 0.001, std_of_returns: float = 0.02,
                                    a_coeff: float = -0.25, b_coeff: float = 1.25, intercept: float = 0.004)\
        -> Tuple[SimpleReturnsSeries, SimpleReturnsDataFrame]:
    """
    Creates a dataframe with simple returns of sample timeseries (regressors). Then creates a series which linearly
    depends on regressors 'a' and 'b'.
    """
    dates = pd.bdate_range(start=start_date, periods=dates_span)
    regressors_names = generate_sample_column_names(num_of_columns=num_of_regressors)
    # init random number generator with a fixed number, so that results are always the same
    random_state = np.random.RandomState(5)

    regressors_data = random_state.normal(mean_return, std_of_returns, (dates_span, num_of_regressors))
    regressors_df = SimpleReturnsDataFrame(data=regressors_data, index=dates, columns=regressors_names)

    analyzed_data = a_coeff * regressors_data[:, 0] + b_coeff * regressors_data[:, 1] + \
        random_state.normal(0, 0.02, dates_span) + intercept

    analysed_tms = SimpleReturnsSeries(data=analyzed_data, index=dates, name='Fund')

    return analysed_tms, regressors_df
