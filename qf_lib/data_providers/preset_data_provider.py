from datetime import datetime
from typing import Union, Sequence, Set, Type

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.data_providers.price_data_provider import DataProvider


class PresetDataProvider(DataProvider):
    """
    Wrapper on QFDataArray which makes it a DataProvider.
    """

    def __init__(self, data: QFDataArray, start_date: datetime, end_date: datetime,
                 check_data_availability: bool = True):
        """
        Parameters
        ----------
        data
            data to be wrapped
        start_date
            beginning of the cached period (not necessarily the first date in the `data`)
        end_date
            end of the cached period (not necessarily the last date in the `data`)
        check_data_availability
            True by default. If False then if there's a call for a non-existent piece of data, some strange behaviour
            may occur (e.g. nans returned).
        """
        self._data_bundle = data
        self._check_data_availability = check_data_availability

        if self._check_data_availability:
            self._tickers_cached_set = set(data.tickers.values)
            self._fields_cached_set = set(data.fields.values)
            self._start_date = start_date
            self._end_date = end_date

        self._ticker_types = {type(ticker) for ticker in data.tickers.values}

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                  fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None
                  ) -> Union[None, PricesSeries, PricesDataFrame, QFDataArray]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, PriceField)
        got_single_date = start_date is not None and (start_date == end_date)

        if self._check_data_availability:
            self._check_if_cached_data_available(tickers, fields, start_date, end_date)

        data_array = self._data_bundle.loc[start_date:end_date, tickers, fields]
        normalized_result = normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker,
                                                 got_single_field, use_prices_types=True)

        return normalized_result

    def _check_if_cached_data_available(self, tickers, fields, start_date, end_date):
        # tickers which are not cached but were requested
        uncached_tickers = set(tickers) - self._tickers_cached_set
        if uncached_tickers:
            raise ValueError("Tickers: {} are not available in the Data Bundle".format(tickers))

        # fields which are not cached but were requested
        uncached_fields = set(fields) - self._fields_cached_set
        if uncached_fields:
            raise ValueError("Fields: {} are not available in the Data Bundle".format(fields))

        if start_date < self._start_date or end_date > self._end_date:
            raise ValueError("Requested dates are outside of the cached period")

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]],
                    fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, **kwargs
                    ) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        raise NotImplementedError()

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return self._ticker_types
