import warnings
from datetime import datetime
from typing import Union, Sequence, Set, Type

import pandas as pd

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


class PrefetchingDataProvider(DataProvider):
    """
    Optimises running of the DataProvider by pre-fetching all the data at startup and then using the cached data
    instead of sending over-the-network requests every time the data is requested. If not all data requested
    is available the ValueError will be raised.
    """

    def __init__(self, data_provider: DataProvider,
                 tickers: Sequence[Ticker],
                 fields: Sequence[PriceField],
                 start_date: datetime, end_date: datetime):
        self.data_provider = data_provider

        self._data_bundle = self.data_provider.get_price(tickers, fields, start_date, end_date)
        self._tickers_cached = tickers
        self._fields_cached = fields
        self._start_date = start_date
        self._end_date = end_date

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                  fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None
                  ) -> Union[None, PricesSeries, PricesDataFrame, QFDataArray]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, PriceField)
        got_single_date = (start_date == end_date)

        self._check_if_cached_data_available(tickers, fields, start_date, end_date)

        data_array = self._data_bundle.loc[start_date:end_date, tickers, fields]
        normalized_result = normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker,
                                                 got_single_field, use_prices_types=True)

        return normalized_result

    def _check_if_cached_data_available(self, tickers, fields, start_date, end_date):
        # tickers which are not cached but were requested
        uncached_tickers = [ticker for ticker in tickers if ticker not in self._tickers_cached]
        if uncached_tickers:
            raise ValueError("Tickers: {} are not available in the Data Bundle".format(tickers))

        # fields which are not cached but were requested
        uncached_fields = [field for field in fields if field not in self._fields_cached]
        if uncached_fields:
            raise ValueError("Fields: {} are not available in the Data Bundle".format(fields))

        if start_date < self._start_date or end_date > self._end_date:
            raise ValueError("Requested dates are outside of the cached period".format(fields))

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]],
                    fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, **kwargs
                    ) -> Union[QFSeries, QFDataFrame, pd.Panel]:
        warnings.warn("get_history() using the cached data is not supported yet. Normal request is being sent instead")
        return self.data_provider.get_history(tickers, fields, start_date, end_date, **kwargs)

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return self.data_provider.supported_ticker_types()
