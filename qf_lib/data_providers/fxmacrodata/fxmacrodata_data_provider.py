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
from typing import Dict, Optional, Sequence, Set, Type, Union
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import FXMacroDataTicker, Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.helpers import normalize_data_array


class FXMacroDataDataProvider(AbstractPriceDataProvider):
    """
    Data Provider using FXMacroData to provide daily FX spot rates.

    Parameters
    ----------
    api_key: Optional[str]
        FXMacroData API key. If omitted, ``FXMACRODATA_API_KEY`` and
        ``FXMD_API_KEY`` environment variables are checked.
    base_url: str
        FXMacroData API base URL.
    timeout: float
        HTTP request timeout in seconds.
    timer: Optional[Timer]
        Timer used by QF-Lib for look-ahead-bias handling.
    """

    _api_key_env_vars = ('FXMACRODATA_API_KEY', 'FXMD_API_KEY')
    _max_pages = 1000

    def __init__(
            self, api_key: Optional[str] = None, base_url: str = 'https://api.fxmacrodata.com/v1',
            timeout: float = 30, timer: Optional[Timer] = None):
        super().__init__(timer)
        self.api_key = api_key or self._get_env_api_key()
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def price_field_to_str_map(self, *args) -> Dict[PriceField, str]:
        return {
            PriceField.Open: 'Open',
            PriceField.High: 'High',
            PriceField.Low: 'Low',
            PriceField.Close: 'Close',
            PriceField.Volume: 'Volume'
        }

    def get_history(
            self, tickers: Union[FXMacroDataTicker, Sequence[FXMacroDataTicker]],
            fields: Union[None, str, PriceField, Sequence[Union[str, PriceField]]],
            start_date: datetime, end_date: datetime = None, frequency: Frequency = None,
            look_ahead_bias: bool = False, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical daily FX spot data from FXMacroData.
        """
        frequency = frequency or self.frequency or Frequency.DAILY
        if frequency != Frequency.DAILY:
            raise ValueError('FXMacroDataDataProvider supports daily data only.')

        original_end_date = (end_date or self.timer.now()) + RelativeDelta(second=0, microsecond=0)
        original_end_date += RelativeDelta(hour=23, minute=59)
        end_date = original_end_date if look_ahead_bias else self.get_end_date_without_look_ahead(
            original_end_date, frequency)
        start_date = self._adjust_start_date(start_date, frequency)
        got_single_date = self._got_single_date(start_date, original_end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, FXMacroDataTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))
        fields = self._normalise_fields(fields)

        tickers_data = {
            ticker: self._get_rows(ticker, start_date, end_date)
            for ticker in tickers
        }
        data_array = self._rows_to_data_array(tickers_data, tickers, fields)
        return normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=False
        )

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return {FXMacroDataTicker}

    @classmethod
    def _get_env_api_key(cls) -> Optional[str]:
        for name in cls._api_key_env_vars:
            value = os.getenv(name)
            if value:
                return value
        return None

    def _normalise_fields(self, fields: Sequence[Union[str, PriceField]]) -> Sequence[str]:
        field_map = self.price_field_to_str_map()
        supported_fields = set(field_map.values())
        normalised_fields = [
            field_map[field] if isinstance(field, PriceField) else field
            for field in fields
        ]
        unsupported_fields = [field for field in normalised_fields if field not in supported_fields]
        if unsupported_fields:
            raise LookupError(
                f'Fields {unsupported_fields} are not recognised by the data provider. '
                f'Available Fields: {list(supported_fields)}'
            )
        return normalised_fields

    def _get_rows(
            self, ticker: FXMacroDataTicker, start_date: datetime, end_date: datetime) -> Sequence[dict]:
        # The API returns at most 100 rows per request (newest first), so page through
        # the window with offset until pagination.has_more is false.
        rows = []
        offset = 0
        for _ in range(self._max_pages):
            params = urlencode({
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'limit': 100,
                'offset': offset,
            })
            url = (
                f'{self.base_url}/forex/{ticker.base_ccy.lower()}/{ticker.quote_ccy.lower()}?{params}'
            )
            request = Request(url)
            if self.api_key:
                request.add_header('X-API-Key', self.api_key)
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode('utf-8'))
            if isinstance(payload, list):
                return rows + payload
            if not isinstance(payload, dict):
                break
            page = payload.get('data') or []
            rows.extend(page)
            pagination = payload.get('pagination')
            if not page or not isinstance(pagination, dict) or not pagination.get('has_more'):
                break
            offset = pagination.get('next_offset') or offset + len(page)
        return rows

    def _rows_to_data_array(
            self, tickers_data: Dict[FXMacroDataTicker, Sequence[dict]],
            tickers: Sequence[FXMacroDataTicker], fields: Sequence[str]) -> QFDataArray:
        ticker_values = {}
        dates = set()
        for ticker, rows in tickers_data.items():
            values_by_date = {}
            for row in rows:
                date = row.get('date')
                rate = self._get_rate(row)
                if date is None or rate is None:
                    continue
                date = pd.to_datetime(date).to_pydatetime()
                values_by_date[date] = rate
                dates.add(date)
            ticker_values[ticker] = values_by_date

        dates = pd.DatetimeIndex(sorted(dates))
        data = np.empty((len(dates), len(tickers), len(fields)))
        data[:] = np.nan
        date_positions = {date.to_pydatetime(): idx for idx, date in enumerate(dates)}

        for ticker_idx, ticker in enumerate(tickers):
            for date, rate in ticker_values.get(ticker, {}).items():
                for field_idx, field in enumerate(fields):
                    data[date_positions[date], ticker_idx, field_idx] = 0 if field == 'Volume' else rate

        return QFDataArray.create(dates, tickers, fields, data)

    @staticmethod
    def _get_rate(row: dict) -> Optional[float]:
        for key in ('val', 'value', 'close', 'rate'):
            value = row.get(key)
            if value is not None:
                return float(value)
        return None
