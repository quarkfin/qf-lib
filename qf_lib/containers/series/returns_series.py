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

from datetime import datetime
from typing import Union

from pandas import DatetimeIndex, Timedelta, Index

from qf_lib.containers.series.qf_series import QFSeries


class ReturnsSeries(QFSeries):
    """
    Series of returns. It is a base class for series which specify the type of the returns (e.g. LogReturnsSeries).
    This is an abstract class and should not be instantiated.
    """

    @property
    def _constructor(self):
        raise NotImplementedError()

    @property
    def _constructor_expanddim(self):
        raise NotImplementedError()

    def to_prices(self, initial_price: float = None, suggested_initial_date: Union[datetime, int, float] = None,
                  frequency=None) -> "PricesSeries":
        if suggested_initial_date is None:
            suggested_initial_date = self._get_initial_date(frequency)
        if initial_price is None:
            initial_price = 1.0

        if suggested_initial_date is not datetime:
            prices_dates = Index([suggested_initial_date]).append(self.index.copy())  # if it is numeric or string based
        else:
            prices_dates = DatetimeIndex([suggested_initial_date]).append(self.index.copy())

        prices_values = self._to_prices_values(initial_price)

        from qf_lib.containers.series.prices_series import PricesSeries
        return PricesSeries(data=prices_values, index=prices_dates).__finalize__(self)

    def _get_initial_date(self, frequency=None):
        if frequency is None:
            interval, _ = self.infer_interval()
        else:
            interval = Timedelta(frequency.nr_of_calendar_days(), unit='D')

        first_date = self.index[0]
        return first_date - interval

    def _to_prices_values(self, initial_price):
        # method must be implemented by classes inheriting from ReturnsSeries
        raise NotImplementedError()
