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
from typing import Dict, Union, Sequence

from pandas import concat

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class FuturesPresetDataProvider(PresetDataProvider):
    def __init__(self, data: Union[None, PricesSeries, PricesDataFrame, QFDataArray],
                 exp_dates: Dict[Ticker, QFSeries],
                 start_date: datetime, end_date: datetime,
                 frequency: Frequency, check_data_availability: bool = True):
        """
        Parameters
        ----------
        data
            data to be wrapped. It is of dictionary type and provides a mapping from Tickers onto a Tuple representing
            a data_array, considering all tickers belonging to the Tickers futures chain, and a series representing the
            expiration dates of all futures contracts from the chain.
        exp_dates
            dictionary mapping FutureTickers to QFSeries of contracts expiration dates, belonging to the certain
            future ticker family
        start_date
            beginning of the cached period (not necessarily the first date in the `data`)
        end_date
            end of the cached period (not necessarily the last date in the `data`)
        frequency
            frequency of the data
        check_data_availability
            True by default. If False then if there's a call for a non-existent piece of data, some strange behaviour
            may occur (e.g. nans returned).
        """

        super().__init__(data, start_date, end_date, frequency, check_data_availability)
        self._exp_dates = exp_dates

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]], date: datetime,
                                  include_expired_contracts: bool = True) -> Dict[FutureTicker, QFSeries]:

        if not isinstance(tickers, Sequence):
            tickers = [tickers]

        def get_futures_expiration_dates(tickers_list: Sequence[Ticker]) -> QFSeries:
            partial_results = []

            for exp_dates_series in self._exp_dates.values():
                # Find all the expiration dates corresponding to any ticker from tickers and append them to the
                # partial_results list
                partial_result = exp_dates_series.where(exp_dates_series.isin(tickers_list)).dropna()
                partial_results.append(partial_result)

            # Concatenate the partial results and cast the series to QFSeries
            exp_dates = concat(partial_results)
            exp_dates = cast_series(exp_dates, QFSeries)
            return exp_dates

        if include_expired_contracts:
            future_chain_tickers = {
                ticker: get_futures_expiration_dates(
                    list(self._exp_dates[ticker].values)
                )
                for ticker in tickers
            }
        else:
            # In case of passing the include_expired_contracts = False argument, all expired contracts (whose expiration
            # date < current time), should be excluded from the returned tickers lists
            def extract_non_expired(ticker):
                # Get the list of all futures contracts tickers
                exp_dates = self._exp_dates[ticker]
                # Filter out the expired contracts
                exp_dates = exp_dates[exp_dates.index >= date]
                return list(exp_dates.values)

            future_chain_tickers = {
                ticker: get_futures_expiration_dates(extract_non_expired(ticker))
                for ticker in tickers
            }

        return future_chain_tickers

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY):

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)

        tickers_mapping = {(t.valid_ticker() if isinstance(t, FutureTicker) else t): t for t in tickers}

        specific_tickers = list(tickers_mapping.keys())
        specific_tickers = specific_tickers[0] if got_single_ticker else specific_tickers

        prices_result = super().get_price(specific_tickers, fields, start_date, end_date, frequency)

        # Map the specific tickers onto the tickers given by the tickers_mapping array
        if isinstance(prices_result, QFDataArray):
            prices_result.tickers.values = [tickers_mapping[t] for t in prices_result.tickers.values]
        elif isinstance(prices_result, PricesDataFrame):
            prices_result = prices_result.rename(columns=tickers_mapping)

        return prices_result

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]],
                    fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY, **kwargs
                    ) -> Union[QFSeries, QFDataFrame, QFDataArray]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)

        tickers_mapping = {(t.valid_ticker() if isinstance(t, FutureTicker) else t): t for t in tickers}

        specific_tickers = list(tickers_mapping.keys())
        specific_tickers = specific_tickers[0] if got_single_ticker else specific_tickers

        prices_result = super().get_history(specific_tickers, fields, start_date, end_date, frequency, **kwargs)

        # Map the specific tickers onto the tickers given by the tickers_mapping array
        if isinstance(prices_result, QFDataArray):
            prices_result.tickers.values = [tickers_mapping[t] for t in prices_result.tickers.values]
        elif isinstance(prices_result, PricesDataFrame):
            prices_result = prices_result.rename(columns=tickers_mapping)

        return prices_result
