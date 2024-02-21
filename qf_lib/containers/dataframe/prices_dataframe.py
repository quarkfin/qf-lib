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
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class PricesDataFrame(QFDataFrame):
    """
    DataFrame containing prices (for example prices of the SPY).
    """
    @property
    def _constructor_sliced(self):
        from qf_lib.containers.series.prices_series import PricesSeries
        return PricesSeries

    @property
    def _constructor(self):
        return PricesDataFrame

    def to_simple_returns(self) -> "SimpleReturnsDataFrame":
        """
        Converts dataframe to the dataframe of simple returns. First date of prices in the returns timeseries won't
        be present.

        Returns
        -------
        SimpleReturnsDataFrame
            dataframe of simple returns
        """
        from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
        returns = self.pct_change(fill_method=None)
        return SimpleReturnsDataFrame(data=returns.iloc[1:], index=self.index[1:]).__finalize__(self)
