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

from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class RollingContractData(object):
    def __init__(self, prices_df: PricesDataFrame, time_to_expiration_tms: pd.Series, returns_tms: SimpleReturnsSeries):
        """
        Parameters
        ----------
        prices_df
            DataFrame for a certain contract (e.g. 1-month contract) with Open, High, Low, Close, Volume as columns.
            It is indexed with time.
        time_to_expiration_tms
            Timeseries showing in how much time the currently held real contract will expire
        returns_tms
            returns of the
        """
        self.prices_df = prices_df
        self.time_to_expiration_tms = time_to_expiration_tms
        self.returns_tms = returns_tms
