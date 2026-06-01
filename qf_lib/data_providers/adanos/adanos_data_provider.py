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

import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Sequence, Set, Type, Union
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array, tickers_dict_to_data_array


class AdanosDataProvider(DataProvider):
    """
    Optional DataProvider for Adanos Market Sentiment API stock sentiment data.

    The provider exposes Adanos sentiment values as alternative data fields through the standard get_history()
    interface. It is intentionally separate from AbstractPriceDataProvider because Adanos does not provide OHLCV
    prices.

    Parameters
    ----------
    api_key
        Adanos API key. If omitted, the provider reads ADANOS_API_KEY from the environment.
    source
        Adanos stock sentiment source: reddit, x, news or polymarket.
    base_url
        API base URL. Defaults to https://api.adanos.org.
    timeout
        HTTP timeout in seconds.

    Examples
    --------
    >>> from qf_lib.common.tickers.tickers import BloombergTicker
    >>> from qf_lib.data_providers.adanos import AdanosDataProvider
    >>> provider = AdanosDataProvider(source="reddit")
    >>> provider.get_history(BloombergTicker("TSLA US Equity"), "sentiment_score", start_date, end_date)
    """

    DEFAULT_FIELDS = ("sentiment_score", "buzz_score", "mentions")
    _SOURCE_PATHS = {
        "reddit": "/reddit/stocks/v1/stock/{ticker}",
        "x": "/x/stocks/v1/stock/{ticker}",
        "news": "/news/stocks/v1/stock/{ticker}",
        "polymarket": "/polymarket/stocks/v1/stock/{ticker}",
    }

    def __init__(
            self, api_key: Optional[str] = None, source: str = "reddit", base_url: str = "https://api.adanos.org",
            timeout: int = 30, timer: Optional[Timer] = None):
        super().__init__(timer)
        self.api_key = api_key or os.environ.get("ADANOS_API_KEY")
        if not self.api_key:
            raise ValueError("AdanosDataProvider requires an api_key or ADANOS_API_KEY environment variable.")

        source = source.lower()
        if source not in self._SOURCE_PATHS:
            raise ValueError("Unsupported Adanos source '{}'. Supported sources are: {}.".format(
                source, ", ".join(sorted(self._SOURCE_PATHS.keys()))))

        self.source = source
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.frequency = Frequency.DAILY

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, frequency: Frequency = None,
            look_ahead_bias: bool = False, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets daily Adanos sentiment attributes for the requested stock tickers.

        Supported fields are string field names returned by the Adanos stock sentiment endpoint, for example
        sentiment_score, buzz_score, mentions, bullish_pct or bearish_pct. If a daily trend series is available in
        the API response, rows are dated with its daily dates. Otherwise the summary response is returned as one row
        dated at end_date.
        """
        frequency = frequency or self.frequency
        if frequency != Frequency.DAILY:
            raise ValueError("AdanosDataProvider supports daily sentiment data only.")

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, str)
        if look_ahead_bias:
            end_date = end_date or self.timer.now()
        else:
            end_date = self.get_end_date_without_look_ahead(end_date, frequency)
        got_single_date = start_date.date() == end_date.date()

        tickers_data_dict = {}
        for ticker in tickers:
            self._validate_stock_ticker(ticker)
            ticker_symbol = self._ticker_to_symbol(ticker)
            payload = self._get_stock_sentiment(ticker_symbol, start_date, end_date)
            ticker_df = self._payload_to_dataframe(payload, fields, end_date)
            if not ticker_df.empty:
                tickers_data_dict[ticker] = ticker_df

        data_array = tickers_dict_to_data_array(tickers_data_dict, tickers, fields)
        return normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field)

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return {Ticker}

    def _get_stock_sentiment(self, ticker_symbol: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        path = self._SOURCE_PATHS[self.source].format(ticker=quote(ticker_symbol))
        params = {
            "from": start_date.date().isoformat(),
            "to": end_date.date().isoformat(),
        }
        return self._request_json(path, params)

    def _request_json(self, path: str, params: Dict[str, str]) -> Dict[str, Any]:
        url = "{}{}?{}".format(self.base_url, path, urlencode(params))
        request = Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "qf-lib-adanos-data-provider",
            "X-API-Key": self.api_key,
        })
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _validate_stock_ticker(ticker: Ticker) -> None:
        if ticker.security_type != SecurityType.STOCK:
            raise ValueError("AdanosDataProvider supports stock tickers only.")

    @staticmethod
    def _ticker_to_symbol(ticker: Ticker) -> str:
        ticker_str = ticker.as_string().strip()
        if ticker_str.startswith("$"):
            ticker_str = ticker_str[1:]
        return ticker_str.split()[0].upper()

    @classmethod
    def _payload_to_dataframe(cls, payload: Dict[str, Any], fields: Sequence[str], end_date: datetime) -> QFDataFrame:
        if payload.get("found") is False:
            return QFDataFrame(columns=fields)

        daily_rows = cls._daily_rows(payload, fields)
        if daily_rows:
            return QFDataFrame.from_dict(daily_rows, orient="index").reindex(columns=fields).sort_index()

        summary_row = cls._row_from_mapping(payload, fields)
        if all(value is None for value in summary_row.values()):
            return QFDataFrame(columns=fields)

        return QFDataFrame([summary_row], index=[cls._date_from_value(end_date)]).reindex(columns=fields)

    @classmethod
    def _daily_rows(cls, payload: Dict[str, Any], fields: Sequence[str]) -> Dict[datetime, Dict[str, Any]]:
        rows = {}
        for item in cls._iter_daily_items(payload):
            if not isinstance(item, dict) or "date" not in item:
                continue

            date = cls._date_from_value(item["date"])
            rows[date] = cls._row_from_mapping(item, fields, fallback=payload)
        return rows

    @staticmethod
    def _iter_daily_items(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        for key in ("daily_trend", "trend_history", "history", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    yield item

    @staticmethod
    def _row_from_mapping(mapping: Dict[str, Any], fields: Sequence[str],
                          fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        fallback = fallback or {}
        return {field: mapping.get(field, fallback.get(field)) for field in fields}

    @staticmethod
    def _date_from_value(value: Union[str, datetime]) -> datetime:
        return pd.Timestamp(value).to_pydatetime().replace(hour=0, minute=0, second=0, microsecond=0)
