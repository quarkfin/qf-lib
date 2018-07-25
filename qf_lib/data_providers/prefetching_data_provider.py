from datetime import datetime
from typing import Union, Sequence, Set, Type

import pandas as pd

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import squeeze_panel, cast_result_to_proper_type
from qf_lib.data_providers.price_data_provider import DataProvider


class PrefetchingDataProvider(DataProvider):
    """
    Optimises running of the DataProvider by pre-fetching all the data at startup and then using the cached data
    instead of sending over-the-network requests every time the data is requested from it. If not all data requested
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

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                  fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None
                  ) -> Union[None, PricesSeries, PricesDataFrame, pd.Panel]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(tickers, PriceField)
        got_single_date = (start_date == end_date)

        self._check_if_cached_data_available(fields, tickers)

        panel = self._data_bundle.loc[start_date:end_date, tickers, fields]

        squeezed_result = squeeze_panel(panel, got_single_date, got_single_ticker, got_single_field)
        casted_result = cast_result_to_proper_type(squeezed_result)

        return casted_result

    def _check_if_cached_data_available(self, fields, tickers):
        # tickers which are not cached but were requested
        uncached_tickers = [ticker for ticker in tickers if ticker not in self._tickers_cached]
        if uncached_tickers:
            raise ValueError("Tickers: {} are not available in the Data Bundle".format(tickers))

        # fields which are not cached but were requested
        uncached_fields = [field for field in fields if field not in self._fields_cached]
        if uncached_fields:
            raise ValueError("Fields: {} are not available in the Data Bundle".format(fields))

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]],
                    fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, **kwargs
                    ) -> Union[QFSeries, QFDataFrame, pd.Panel]:
        pass

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return self.data_provider.supported_ticker_types()
