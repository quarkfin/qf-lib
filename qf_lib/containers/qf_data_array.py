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

from collections import OrderedDict
from datetime import datetime
from typing import Sequence, Union, Dict, Hashable

import numpy as np
import pandas as pd
import xarray as xr
from xarray.core import dtypes

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import FIELDS, TICKERS, DATES


class QFDataArray(xr.DataArray):

    def __init__(self, data, coords=None, dims=None, name=None, attrs=None, indexes: Dict[Hashable, pd.Index] = None,
                 fastpath=False):
        """
        Use the class method `create()` for creating QFDataArrays.
        DO NOT CREATE QFDataArrays using __init__() method (don't create it like this: QFDataArray()).
        The __init__ method should be used only by xr.DataArray internal methods.

        Important: Regardless of the xarray warning message the __slots__ should not be implemented, as they result
        in Recursion Error.
        """
        if not fastpath:
            self._check_if_dimensions_are_correct(coords, dims)

        super().__init__(data, coords, dims, name, attrs, indexes, fastpath)

    def __setattr__(self, name, value):
        # Makes it possible to set indices in this way: qf_data_array.fields = ["OPEN", "CLOSE"].
        # Otherwise one would need to set them like this: qf_data_array[FIELDS] = ["OPEN", "CLOSE"]
        # if name == TICKERS or name == DATES or name == FIELDS:
        if name in [FIELDS, TICKERS, DATES]:
            self.__setitem__(name, value)
        else:
            super().__setattr__(name, value)

    @classmethod
    def create(cls, dates: Union[Sequence[datetime], pd.DatetimeIndex],
               tickers: Union[Sequence[str], Sequence[Ticker]],
               fields: Union[Sequence[PriceField], Sequence[str]],
               data=None, name=None) -> "QFDataArray":
        """
        Helper method for creating a QFDataArray. __init__() methods can't be used for that, because its signature
        must be the same as the signature of xr.DataArray.__init__().

        Example: a = QFDataArray.create(dates=pd.date_range('2017-01-01', periods=3), tickers=['a', 'b'],
        fields=['field'], data=[[[1.0], [2.0]], [[3.0], [4.0]], [[5.0], [6.0]]])

        Parameters
        ----------
        dates
            dates index (labels)
        tickers
            tickers index (labels)
        fields
            fields index (labels)
        data
            data that should be put in the array (it's dimensions must be in the proper order: dates, tickers, fields).
        name
            name of the QFDataArray

        Returns
        -------
        QFDataArray
        """
        coordinates = {DATES: dates, TICKERS: tickers, FIELDS: fields}
        dimensions = (DATES, TICKERS, FIELDS)

        # if no data is provided, the empty array will be created
        if data is None:
            data = np.empty((len(dates), len(tickers), len(fields)))
            data[:] = np.nan

        return QFDataArray(data, coordinates, dimensions, name)

    @classmethod
    def from_xr_data_array(cls, xr_data_array: xr.DataArray) -> "QFDataArray":
        """
        Converts regular xr.DataArray into QFDataArray.

        Parameters
        ----------
        xr_data_array
            xr.DataArray with 3 dimensions: dates, tickers and fields.

        Returns
        -------
        QFDataArray
        """
        xr_data_array = xr_data_array.transpose(DATES, TICKERS, FIELDS)
        qf_data_array = QFDataArray.create(
            xr_data_array.dates, xr_data_array.tickers, xr_data_array.fields, xr_data_array.data, xr_data_array.name)
        return qf_data_array

    @classmethod
    def concat(cls, objs, dim, data_vars='all', coords='different', compat='equals', positions=None,
               fill_value=dtypes.NA, join='outer', combine_attrs='override') -> "QFDataArray":
        """
        Concatenates different xr.DataArrays and then converts the result to QFDataArray.

        See Also
        --------
        xr.concat()
        """
        result = xr.concat(
            objs, dim, data_vars, coords, compat, positions, fill_value, join, combine_attrs)  # type: xr.DataArray
        result = QFDataArray.from_xr_data_array(result)

        return result

    def asof(self, dates: Union[datetime, Sequence[datetime]]) -> QFDataFrame:
        tickers = self.tickers.values
        fields = self.fields.values

        if isinstance(dates, datetime):
            dates = [dates] * len(tickers)
        elif len(dates) != len(tickers):
            raise ValueError("Number of dates must be equal to the number of tickers")

        asof_values = np.empty((len(tickers), len(fields)))

        for i, (ticker, date) in enumerate(zip(tickers, dates)):
            ticker_data = self.loc[:, ticker, :]
            ticker_df = QFDataFrame(ticker_data.to_pandas())  # type: QFDataFrame
            data_asof = ticker_df.asof(date)
            asof_values[i, :] = data_asof

        result = QFDataFrame(data=asof_values, index=self.tickers.to_index(), columns=self.fields.to_index())
        return result

    def _check_if_dimensions_are_correct(self, coords, dims):
        expected_dimensions = (DATES, TICKERS, FIELDS)
        if dims is not None:
            actual_dimensions = tuple(dims)
        elif coords is not None and isinstance(coords, OrderedDict):
            actual_dimensions = tuple(coords.keys())
        else:
            actual_dimensions = None
        if actual_dimensions != expected_dimensions:
            raise ValueError("Dimensions must be equal to: {}".format(expected_dimensions))
