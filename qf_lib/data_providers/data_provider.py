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
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union, Sequence, Type, Set

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries


class DataProvider(object, metaclass=ABCMeta):
    """ An interface for data providers (for example AbstractPriceDataProvider or GeneralPriceProvider). """

    frequency = None

    def __init__(self):
        self.logger = qf_logger.getChild(self.__class__.__name__)

    @abstractmethod
    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[None, str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, frequency: Frequency = None, **kwargs) -> Union[
                QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical attributes (fields) of different securities (tickers).

        All the duplicate fields and tickers will be removed (the first occurrence will remain). This is crucial
        for having the expected behavior with using label-based indices. E.g. let's assume there is a duplicate ticker
        'SPX Index' in tickers list and the result data frame has two columns 'SPX Index'. Then when someone
        runs result.loc[:, 'SPX Index'], he expects to get a series of 'SPX Index' values. However
        he'll get a data frame with two columns, both named 'SPX Index'.
        If someone insists on keeping duplicate values in index/columns, then it's possible to reindex the result
        (e.g. result.reindex(columns=tickers)).

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            tickers for securities which should be retrieved
        fields: None, str, Sequence[str]
            fields of securities which should be retrieved. If None, all available fields will be returned
            (only supported by few DataProviders)
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        frequency: Frequency
            frequency of the data
        kwargs
            kwargs should not be used on the level of AbstractDataProvider. They are here to provide a common interface
            for all data providers since some of the specific data providers accept additional arguments

        Returns
        -------
        QFSeries, QFDataFrame, QFDataArray
            If possible the result will be squeezed, so that instead of returning QFDataArray, data of lower
            dimensionality will be returned. The results will be either an QFDataArray (with 3 dimensions: date, ticker,
            field), a QFDataFrame (with 2 dimensions: date, ticker or field; it is also possible to get 2 dimensions
            ticker and field if single date was provided) or QFSeries (with 1 dimensions: date).
            If no data is available in the database or an non existing ticker was provided an empty structure
            (QFSeries, QFDataFrame or QFDataArray) will be returned returned.
        """
        pass

    @abstractmethod
    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        """
        Returns classes of tickers which are supported by this DataProvider.
        """
        pass

    def __str__(self):
        return self.__class__.__name__
