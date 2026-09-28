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
from unittest.mock import patch

import pytest

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import FXMacroDataTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.fxmacrodata.fxmacrodata_data_provider import FXMacroDataDataProvider


API_KEY = 'api_key'


class FXMacroDataResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode('utf-8')


@pytest.fixture
def provider():
    return FXMacroDataDataProvider(api_key=API_KEY, base_url='https://example.com/v1')


def test_fxmacrodata_ticker_from_string():
    ticker = FXMacroDataTicker.from_string('EUR/USD')

    assert ticker.as_string() == 'EURUSD'
    assert ticker.name == 'EUR/USD'
    assert ticker.base_ccy == 'EUR'
    assert ticker.quote_ccy == 'USD'


@patch('qf_lib.data_providers.fxmacrodata.fxmacrodata_data_provider.urlopen')
def test_get_price__single_ticker_many_fields(mock_urlopen, provider):
    mock_urlopen.return_value = FXMacroDataResponse({
        'data': [
            {'date': '2024-01-02', 'val': '1.101'},
            {'date': '2024-01-03', 'val': 1.102},
        ]
    })

    result = provider.get_price(
        FXMacroDataTicker('EURUSD'),
        [PriceField.Open, PriceField.Close, PriceField.Volume],
        str_to_date('2024-01-02'),
        str_to_date('2024-01-03'),
        Frequency.DAILY,
        look_ahead_bias=True
    )

    request = mock_urlopen.call_args.args[0]
    assert request.full_url == (
        'https://example.com/v1/forex/eur/usd?'
        'start_date=2024-01-02&end_date=2024-01-03&limit=100&offset=0'
    )
    assert dict(request.header_items())['X-api-key'] == API_KEY
    assert mock_urlopen.call_args.kwargs['timeout'] == 30
    assert isinstance(result, PricesDataFrame)
    assert list(result.columns) == [PriceField.Open, PriceField.Close, PriceField.Volume]
    assert result[PriceField.Open].tolist() == [1.101, 1.102]
    assert result[PriceField.Close].tolist() == [1.101, 1.102]
    assert result[PriceField.Volume].tolist() == [0.0, 0.0]


@patch('qf_lib.data_providers.fxmacrodata.fxmacrodata_data_provider.urlopen')
def test_get_price__single_field_many_tickers(mock_urlopen, provider):
    mock_urlopen.side_effect = [
        FXMacroDataResponse({'data': [{'date': '2024-01-02', 'val': 1.101}]}),
        FXMacroDataResponse({'data': [{'date': '2024-01-02', 'val': 1.252}]}),
    ]

    result = provider.get_price(
        [FXMacroDataTicker('EURUSD'), FXMacroDataTicker('GBPUSD')],
        PriceField.Close,
        str_to_date('2024-01-02'),
        str_to_date('2024-01-02'),
        Frequency.DAILY,
        look_ahead_bias=True
    )

    assert isinstance(result, PricesSeries)
    assert result.loc[FXMacroDataTicker('EURUSD')] == 1.101
    assert result.loc[FXMacroDataTicker('GBPUSD')] == 1.252


@patch('qf_lib.data_providers.fxmacrodata.fxmacrodata_data_provider.urlopen')
def test_get_price__follows_pagination(mock_urlopen, provider):
    mock_urlopen.side_effect = [
        FXMacroDataResponse({
            'data': [{'date': '2024-01-04', 'val': 1.104}, {'date': '2024-01-03', 'val': 1.103}],
            'pagination': {'has_more': True, 'next_offset': 2},
        }),
        FXMacroDataResponse({
            'data': [{'date': '2024-01-02', 'val': 1.102}],
            'pagination': {'has_more': False, 'next_offset': None},
        }),
    ]

    result = provider.get_price(
        FXMacroDataTicker('EURUSD'),
        PriceField.Close,
        str_to_date('2024-01-02'),
        str_to_date('2024-01-04'),
        Frequency.DAILY,
        look_ahead_bias=True
    )

    urls = [call.args[0].full_url for call in mock_urlopen.call_args_list]
    assert urls[0].endswith('limit=100&offset=0')
    assert urls[1].endswith('limit=100&offset=2')
    assert result.tolist() == [1.102, 1.103, 1.104]


def test_get_history__unsupported_frequency(provider):
    with pytest.raises(ValueError, match='daily data only'):
        provider.get_price(
            FXMacroDataTicker('EURUSD'),
            PriceField.Close,
            str_to_date('2024-01-02'),
            str_to_date('2024-01-03'),
            Frequency.MIN_1
        )


def test_fxmacrodata_ticker__invalid_pair():
    with pytest.raises(ValueError, match='currency pairs'):
        FXMacroDataTicker('EUR')


@patch('qf_lib.data_providers.fxmacrodata.fxmacrodata_data_provider.urlopen')
def test_get_price__uses_env_api_key(mock_urlopen, monkeypatch):
    monkeypatch.delenv('FXMACRODATA_API_KEY', raising=False)
    monkeypatch.setenv('FXMD_API_KEY', 'env_key')
    provider = FXMacroDataDataProvider(base_url='https://example.com/v1')
    mock_urlopen.return_value = FXMacroDataResponse({'data': []})

    provider.get_price(
        FXMacroDataTicker('EURUSD'),
        PriceField.Close,
        str_to_date('2024-01-02'),
        str_to_date('2024-01-03'),
        Frequency.DAILY,
        look_ahead_bias=True
    )

    request = mock_urlopen.call_args.args[0]
    assert dict(request.header_items())['X-api-key'] == 'env_key'
