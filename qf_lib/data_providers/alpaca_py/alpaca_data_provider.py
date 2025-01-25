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
import itertools
import warnings
from datetime import datetime
from typing import Set, Type, Union, Sequence, Dict, Optional, List

from pandas import MultiIndex, concat, DataFrame

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer, SettableTimer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.alpaca_py.alpaca_ticker import AlpacaTicker
from qf_lib.data_providers.helpers import normalize_data_array

try:
    from alpaca.data import StockHistoricalDataClient, StockBarsRequest, TimeFrame, CryptoHistoricalDataClient, \
    CryptoBarsRequest

    is_alpaca_intalled = True
except ImportError:
    is_alpaca_intalled = False


class AlpacaDataProvider(AbstractPriceDataProvider):

    _security_type_to_request = {
        SecurityType.STOCK: StockBarsRequest,
        SecurityType.CRYPTO: CryptoBarsRequest,
    }

    _security_type_to_function = {
        SecurityType.STOCK: 'get_stock_bars',
        SecurityType.CRYPTO: 'get_crypto_bars',
    }

    def __init__(self, timer: Optional[Timer] = None, api_key: Optional[str] = None, secret_key: Optional[str] = None,
                 oauth_token: Optional[str] = None, use_basic_auth: bool = False):
        """
        Data provider using alpaca-py library to provide historical data for stocks and cryptocurrencies.
        Crypto data does not require authentication. Providing API keys will increase tbe rate limit.

        Parameters
        -----------
        timer: Timer
            Might be either SettableTimer or RealTimer depending on the use case. If no parameter is passed, a default
            RealTimer object will be used.
        api_key: str
            Alpaca API key. Defaults to None.
        secret_key: str
            Alpaca API secret key. Defaults to None.
        oauth_token: str
            The oauth token if authenticating via OAuth. Defaults to None.
        use_basic_auth: bool
            If true, API requests will use basic authorization headers.
        """
        super().__init__(timer)

        if not is_alpaca_intalled:
            warnings.warn(f"alpaca-py ist not installed. If you would like to use {self.__class__.__name__} first"
                          f" install the alpaca-py library.")
            exit(1)

        params = {
            "api_key": api_key,
            "secret_key": secret_key,
            "oauth_token": oauth_token,
            "use_basic_auth": use_basic_auth
        }
        self.security_type_to_client = {
            SecurityType.STOCK: StockHistoricalDataClient(**params),
            SecurityType.CRYPTO: CryptoHistoricalDataClient(**params),
        }

    def price_field_to_str_map(self, *args) -> Dict[PriceField, str]:
        return {
            PriceField.Open: 'open',
            PriceField.High: 'high',
            PriceField.Low: 'low',
            PriceField.Close: 'close',
            PriceField.Volume: 'volume'
        }

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[None, str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = None,
                    look_ahead_bias: bool = False, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:

        frequency = frequency or self.frequency or Frequency.DAILY
        original_end_date = (end_date or self.timer.now()) + RelativeDelta(second=0, microsecond=0)
        end_date = original_end_date + RelativeDelta(hour=23, minute=59) if frequency <= Frequency.DAILY \
            else original_end_date
        end_date = end_date if look_ahead_bias else self.get_end_date_without_look_ahead(end_date, frequency)

        start_date = self._adjust_start_date(start_date, frequency)
        got_single_date = self._got_single_date(start_date, original_end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, AlpacaTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        _dfs = []
        _tickers = sorted(tickers, key=lambda t: t.security_type)
        for sec_type, tickers_group in itertools.groupby(_tickers, lambda t: t.security_type):
            _dfs.append(self._request_data(sec_type, tickers_group, fields, start_date, end_date, frequency,
                                           look_ahead_bias))

        df = concat(_dfs, axis=1, ignore_index=False)
        df = df.reindex(columns=MultiIndex.from_product([fields, [t.as_string() for t in tickers]],))
        data_array = QFDataArray.create(df.index, tickers, fields, df.values.reshape(len(df.index), len(tickers), len(fields)))
        return normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=False
        )

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return {AlpacaTicker}

    @staticmethod
    def _frequency_to_timeframe(freq: Frequency):
        frequencies_mapping = {
            Frequency.MIN_1: TimeFrame.Minute,
            Frequency.MIN_60: TimeFrame.Hour,
            Frequency.DAILY: TimeFrame.Day,
            Frequency.WEEKLY: TimeFrame.Week,
            Frequency.MONTHLY: TimeFrame.Month,
        }

        try:
            return frequencies_mapping[freq]
        except KeyError:
            raise ValueError(f"Frequency must be one of the supported frequencies: {frequencies_mapping.keys()}.") \
                from None

    def _request_data(self, sec_type: SecurityType, tickers: Sequence[AlpacaTicker], fields: List[str],
                      start_date: datetime, end_date: datetime,  frequency: Frequency, look_ahead_bias: bool):
        # Sort tickers based on the SecurityType
        tickers_str = [t.as_string() for t in tickers]
        try:
            client = self.security_type_to_client[sec_type]
            request = self._security_type_to_request[sec_type]
            function = self._security_type_to_function[sec_type]
            df = getattr(client, function)(request(
                symbol_or_symbols=tickers_str,  # check if duplicates should be removed
                timeframe=self._frequency_to_timeframe(frequency),
                start=start_date,
                end=end_date
            )).df.reindex(columns=fields)
            df = df.unstack(level=0)

            if not df.empty:
                df.index = df.index.tz_convert(None).values if frequency > Frequency.DAILY else df.index.date
        except KeyError:
            df = DataFrame([], columns=fields)

        return df
