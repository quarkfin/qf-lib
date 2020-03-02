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

from numpy import log, append, nan

from qf_lib.containers.series.returns_series import ReturnsSeries


class SimpleReturnsSeries(ReturnsSeries):
    """
    Series of simple returns.
    """

    @property
    def _constructor(self):
        return SimpleReturnsSeries

    @property
    def _constructor_expanddim(self):
        from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
        return SimpleReturnsDataFrame

    def to_log_returns(self) -> "LogReturnsSeries":
        from qf_lib.containers.series.log_returns_series import LogReturnsSeries
        log_returns = log(self + 1)
        log_returns_tms = LogReturnsSeries(index=self.index.copy(), data=log_returns.values).__finalize__(self)
        return log_returns_tms

    def to_simple_returns(self) -> "SimpleReturnsSeries":
        return self

    def total_cumulative_return(self) -> float:
        return (self + 1.0).prod() - 1.0

    def total_cumulative_returns_keep_nans(self) -> float:
        if self.isna().all():  # If all values in series are Nan
            return nan
        else:
            return self.total_cumulative_return()

    def _to_prices_values(self, initial_price):
        prices_values = append([1], self.values + 1)
        prices_values = prices_values.cumprod()

        return prices_values * initial_price
