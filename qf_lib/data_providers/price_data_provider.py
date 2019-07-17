from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union, Sequence, Type, Set

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class DataProvider(object, metaclass=ABCMeta):
    """
    An interface for price providers (e.g. AbstractPriceDataProvider or GeneralPriceProvider).
    """

    @abstractmethod
    def get_price(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
            start_date: datetime, end_date: datetime = None) -> Union[None, PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Gets adjusted historical Prices (OPEN HIGH LOW CLOSE) and VOLUME

        Parameters
        ----------
        tickers
            tickers for securities which should be retrieved
        fields
            fields of securities which should be retrieved
        start_date
            date representing the beginning of historical period from which data should be retrieved
        end_date
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used

        Returns
        -------
        historical_data
            If possible the result will be squeezed so that instead of returning QFDataArray (3-D structure),
            data of lower dimensionality will be returned.

            QFDataArray with 3 dimensions: dates, tickers, fields
            PricesDataFrame with 2 dimensions: dates, tickers or fields (depending if many tickers or fields were
                provided). It is also possible to get 2 dimensions ticker and field if single date was provided.
            PricesSeries with 1 dimension: dates

            All the containers will be indexed with PriceField whenever possible
            (for example: instead of 'Close' column in the PricesDataFrame there will be PriceField.Close)
        """
        pass

    @abstractmethod
    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[None, str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical attributes(fields) of different securities(tickers).

        All the duplicate fields and tickers will be removed (the first occurrence will remain). This is crucial
        for having the expected behavior with using label-based indices. E.g. let's assume there is a duplicate ticker
        'SPX Index' in :tickers list and the result data frame has two columns 'SPX Index'. Then when someone
        runs result.loc[:, 'SPX Index'], he expects to get a series of 'SPX Index' values. However
        he'll get a data frame with two columns, both named 'SPX Index'.
        If someone insists on keeping duplicate values in index/columns, then it's possible to reindex the result
        (e.g. result.reindex(columns=tickers)).

        Parameters
        ----------
        tickers
            tickers for securities which should be retrieved
        fields
            fields of securities which should be retrieved. If None, all available fields will be returned
            (only supported by few DataProviders)
        start_date
            date representing the beginning of historical period from which data should be retrieved
        end_date
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        kwargs
            kwargs should not be used on the level of AbstractDataProvider. They are here to provide a common interface
            for all data providers since some of the specific data providers accept additional arguments
        Returns
        -------
        historical_data
            If possible the result will be squeezed, so that instead of returning QFDataArray,
            data of lower dimensionality will be returned.

            QFDataArray with 3 dimensions: date, ticker, field
            QFDataFrame  with 2 dimensions: date, ticker or field (depending if many tickers or fields were provided)
                it is also possible to get 2 dimensions ticker and field if single date was provided.
            QFSeries     with 1 dimensions: date

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
