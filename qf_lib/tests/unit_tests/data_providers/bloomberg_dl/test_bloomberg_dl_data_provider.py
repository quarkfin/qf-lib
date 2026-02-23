#     Copyright 2016-present CERN � European Organization for Nuclear Research
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
from unittest.mock import patch, Mock

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_almost_equal

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from pandas.testing import assert_frame_equal, assert_series_equal

from qf_lib.tests.unit_tests.data_providers.bloomberg_dl.conftest import SSE_PATH, RESPONSE_201_CREATED, \
    RESPONSE_400_BAD_REQUEST, mock_used_for__submit_and_download, _delivery_event, \
    get_mock_heartbeat_event, _history_array, _current_df


def test_get_history__single_ticker_single_field_single_date(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    result = data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    assert result == 100.0


def test_get_history__single_ticker_single_field_multiple_dates(data_provider, aapl_ticker):
    dates = [datetime(2025, 6, 5), datetime(2025, 6, 6)]
    data_provider._submit_and_download = Mock(return_value=_history_array(
        dates=dates, data=[[[100.0]], [[101.0]]]))
    result = data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 5), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    expected = QFSeries(
        [100.0, 101.0],
        index=pd.DatetimeIndex(dates, name="dates"),
        name="AAPL US Equity")
    assert_series_equal(result, expected)


def test_get_history__multiple_tickers_multiple_fields_multiple_dates(data_provider, aapl_ticker, msft_ticker):
    dates = [datetime(2025, 6, 5), datetime(2025, 6, 6)]
    data = [[[100.0, 5000], [200.0, 10000]], [[101.0, 5200], [201.0, 10200]]]
    data_provider._submit_and_download = Mock(return_value=_history_array(
        tickers=("AAPL US Equity", "MSFT US Equity"), fields=("PX_LAST", "PX_VOLUME"),
        dates=dates, data=data))
    result = data_provider.get_history(
        tickers=[aapl_ticker, msft_ticker], fields=["PX_LAST", "PX_VOLUME"],
        start_date=datetime(2025, 6, 5), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    assert isinstance(result, QFDataArray) and result.shape == (2, 2, 2)
    assert_array_almost_equal(result.values, np.array(data))
    assert list(result.tickers.values) == [aapl_ticker, msft_ticker]
    assert list(result.fields.values) == ["PX_LAST", "PX_VOLUME"]


def test_get_history__single_ticker_multiple_fields_single_date(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array(
        fields=("PX_LAST", "PX_VOLUME"), data=[[[100.0, 5000]]]))
    result = data_provider.get_history(
        tickers=aapl_ticker, fields=["PX_LAST", "PX_VOLUME"],
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    expected = QFSeries([100.0, 5000.0], index=pd.Index(["PX_LAST", "PX_VOLUME"], name="fields"),
                        name="AAPL US Equity")
    assert_series_equal(result, expected)


def test_get_history__multiple_tickers_single_field_single_date(data_provider, aapl_ticker, msft_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array(
        tickers=("AAPL US Equity", "MSFT US Equity"), data=[[[100.0], [200.0]]]))
    result = data_provider.get_history(
        tickers=[aapl_ticker, msft_ticker], fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    expected = QFSeries([100.0, 200.0], index=pd.Index([aapl_ticker, msft_ticker], name="tickers"),
                        name="PX_LAST")
    assert_series_equal(result, expected)


@pytest.mark.parametrize("frequency", [Frequency.SEMI_ANNUALLY, Frequency.MIN_1],
                         ids=["semi_annually", "min_1"])
def test_get_history__unsupported_frequency_raises(data_provider, aapl_ticker, frequency):
    with pytest.raises(NotImplementedError):
        data_provider.get_history(
            tickers=aapl_ticker, fields="PX_LAST",
            start_date=datetime(2025, 6, 5), end_date=datetime(2025, 6, 6),
            frequency=frequency, look_ahead_bias=True)


@pytest.mark.parametrize("frequency,expected_period", [
    (Frequency.DAILY, "daily"), (Frequency.WEEKLY, "weekly"),
    (Frequency.MONTHLY, "monthly"), (Frequency.QUARTERLY, "quarterly"),
    (Frequency.YEARLY, "yearly"),
])
def test_get_history__payload_period_matches_frequency(data_provider, aapl_ticker,
                                                       frequency, expected_period):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=frequency, look_ahead_bias=True)
    payload = data_provider._submit_and_download.call_args[0][0]
    assert payload['runtimeOptions']['period'] == expected_period


def test_get_history__payload_type_and_date_range(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    payload = data_provider._submit_and_download.call_args[0][0]
    assert payload['@type'] == 'HistoryRequest'
    dr = payload['runtimeOptions']['dateRange']
    assert dr['@type'] == 'IntervalDateRange'
    assert dr['startDate'] == '2025-06-06' and dr['endDate'] == '2025-06-06'


@pytest.mark.parametrize("currency,expected_key", [
    ("USD", "historyPriceCurrency"), (None, None),
], ids=["with_currency", "without_currency"])
def test_get_history__payload_currency(data_provider, aapl_ticker, currency, expected_key):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True, currency=currency)
    payload = data_provider._submit_and_download.call_args[0][0]
    if expected_key:
        assert payload['runtimeOptions']['historyPriceCurrency'] == currency
    else:
        assert 'historyPriceCurrency' not in payload['runtimeOptions']


@pytest.mark.parametrize("pricing_source,should_exist", [
    ("BGN", True), (None, False),
], ids=["with_source", "without_source"])
def test_get_history__payload_pricing_source(data_provider, aapl_ticker, pricing_source, should_exist):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True, pricing_source=pricing_source)
    payload = data_provider._submit_and_download.call_args[0][0]
    if should_exist:
        assert payload['pricingSourceOptions']['prefer']['mnemonic'] == pricing_source
        assert payload['pricingSourceOptions']['@type'] == 'HistoryPricingSourceOptions'
    else:
        assert 'pricingSourceOptions' not in payload


def test_get_history__payload_overrides(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True,
        overrides={"INCLUDE_EXPIRED_CONTRACTS": "Y"})
    payload = data_provider._submit_and_download.call_args[0][0]
    identifier = payload['universe']['contains'][0]
    assert identifier['fieldOverrides'] == [
        {'@type': 'FieldOverride', 'mnemonic': 'INCLUDE_EXPIRED_CONTRACTS', 'override': 'Y'}]


def test_get_history__payload_trigger_and_formatting(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array())
    data_provider.get_history(
        tickers=aapl_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    payload = data_provider._submit_and_download.call_args[0][0]
    assert payload['trigger'] == {'@type': 'SubmitTrigger'}
    assert payload['formatting']['outputMediaType'] == 'application/json'


def test_get_current_values__single_ticker_single_field(data_provider, aapl_ticker):
    data_provider._submit_and_download = lambda p: _current_df()
    assert data_provider.get_current_values(tickers=aapl_ticker, fields="PX_LAST") == 100.0


def test_get_current_values__single_ticker_multiple_fields(data_provider, aapl_ticker):
    data_provider._submit_and_download = lambda p: _current_df(columns=("PX_LAST", "PX_VOLUME"))
    result = data_provider.get_current_values(tickers=aapl_ticker, fields=["PX_LAST", "PX_VOLUME"])
    expected = QFSeries([100.0, 100.0], index=pd.Index(["PX_LAST", "PX_VOLUME"]),
                        name="AAPL US Equity")
    assert_series_equal(result, expected, check_names=False)


def test_get_current_values__multiple_tickers_single_field(data_provider, aapl_ticker, msft_ticker):
    data_provider._submit_and_download = lambda p: _current_df(
        tickers=("AAPL US Equity", "MSFT US Equity"), data={"PX_LAST": [100.0, 200.0]})
    result = data_provider.get_current_values(tickers=[aapl_ticker, msft_ticker], fields="PX_LAST")
    expected = QFSeries([100.0, 200.0], index=pd.Index([aapl_ticker, msft_ticker]),
                        name="PX_LAST")
    assert_series_equal(result, expected, check_names=False)


def test_get_current_values__multiple_tickers_multiple_fields(data_provider, aapl_ticker, msft_ticker):
    data_provider._submit_and_download = lambda p: _current_df(
        tickers=("AAPL US Equity", "MSFT US Equity"), columns=("PX_LAST", "PX_VOLUME"),
        data={"PX_LAST": [100.0, 200.0], "PX_VOLUME": [5000.0, 10000.0]})
    result = data_provider.get_current_values(
        tickers=[aapl_ticker, msft_ticker], fields=["PX_LAST", "PX_VOLUME"])
    expected = QFDataFrame(
        {"PX_LAST": [100.0, 200.0], "PX_VOLUME": [5000.0, 10000.0]},
        index=pd.Index([aapl_ticker, msft_ticker]))
    assert_frame_equal(result, expected, check_names=False)


def test_get_current_values__payload_structure(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_current_df())
    data_provider.get_current_values(tickers=aapl_ticker, fields="PX_LAST")
    payload = data_provider._submit_and_download.call_args[0][0]
    assert payload['@type'] == 'DataRequest'
    assert payload['pricingSourceOptions']['@type'] == 'DataPricingSourceOptions'
    assert payload['fieldList']['@type'] == 'DataFieldList'


def test_get_current_values__with_overrides(data_provider, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_current_df(
        data={"FUT_CHAIN": [["CTH25 Comdty"]]}))
    data_provider.get_current_values(
        tickers=aapl_ticker, fields="FUT_CHAIN",
        overrides={"CHAIN_DATE": "20250610", "INCLUDE_EXPIRED_CONTRACTS": "Y"})
    payload = data_provider._submit_and_download.call_args[0][0]
    mnemonics = {o['mnemonic'] for o in payload['universe']['contains'][0]['fieldOverrides']}
    assert mnemonics == {"CHAIN_DATE", "INCLUDE_EXPIRED_CONTRACTS"}


def test_get_tickers_universe__returns_list_of_tickers(data_provider, spx_ticker):
    members = [
        {"TICKER_AND_EXCH_CODE": "AAPL US", "PERCENT_WEIGHT": "0.07"},
        {"TICKER_AND_EXCH_CODE": "MSFT US", "PERCENT_WEIGHT": "0.06"},
    ]
    with patch.object(data_provider, 'get_current_values', return_value=members):
        result = data_provider.get_tickers_universe(spx_ticker, date=datetime.now())
    assert isinstance(result, list) and len(result) == 2
    assert all(isinstance(t, BloombergTicker) for t in result)


def test_get_tickers_universe_with_weights__returns_series(data_provider, spx_ticker):
    members = [
        {"TICKER_AND_EXCH_CODE": "AAPL US", "PERCENT_WEIGHT": "0.07"},
        {"TICKER_AND_EXCH_CODE": "MSFT US", "PERCENT_WEIGHT": "0.06"},
    ]
    with patch.object(data_provider, 'get_current_values', return_value=members):
        result = data_provider.get_tickers_universe_with_weights(spx_ticker, date=datetime.now())
    expected = QFSeries(
        [0.07, 0.06],
        index=pd.Index([BloombergTicker("AAPL US Equity"), BloombergTicker("MSFT US Equity")]))
    assert_series_equal(result, expected, check_names=False)


def test_get_tickers_universe__display_figi_returns_bbgid_tickers(data_provider, spx_ticker):
    members = [
        {"TICKER_AND_EXCH_CODE": "BBG000B9XRY4", "PERCENT_WEIGHT": "0.07"},
        {"TICKER_AND_EXCH_CODE": "BBG000BPH459", "PERCENT_WEIGHT": "0.06"},
    ]
    with patch.object(data_provider, 'get_current_values', return_value=members):
        result = data_provider.get_tickers_universe(spx_ticker, date=datetime.now(), display_figi=True)
    assert all("/bbgid/" in t.ticker for t in result)


def test_get_tickers_universe_with_weights__invalid_weight_becomes_nan(data_provider, spx_ticker):
    members = [{"TICKER_AND_EXCH_CODE": "AAPL US", "PERCENT_WEIGHT": "N.A."}]
    with patch.object(data_provider, 'get_current_values', return_value=members):
        result = data_provider.get_tickers_universe_with_weights(spx_ticker, date=datetime.now())
    assert len(result) == 1 and np.isnan(result.iloc[0])


@pytest.mark.parametrize("ticker_str,expected_type,expected_value", [
    ("AAPL US Equity", "TICKER", "AAPL US Equity"),
    ("MSFT US Equity", "TICKER", "MSFT US Equity"),
    ("/isin/US0378331005", "ISIN", "US0378331005"),
    ("/ISIN/US0378331005", "ISIN", "US0378331005"),
    ("/cusip/037833100", "CUSIP", "037833100"),
    ("/bbgid/BBG000B9XRY4", "BB_GLOBAL", "BBG000B9XRY4"),
    ("/sedol1/2046251", "SEDOL", "2046251"),
    ("/buid/EQ0000000001", "BB_UNIQUE", "EQ0000000001"),
    ("/wpk/865985", "WPK", "865985"),
    ("/common/001234567", "COMMON_NUMBER", "001234567"),
    ("/cins/A1234B567", "CINS", "A1234B567"),
    ("/cats/12345678", "CATS", "12345678"),
], ids=["standard", "plain", "isin", "isin_upper", "cusip", "bbgid",
        "sedol", "buid", "wpk", "common", "cins", "cats"])
def test__parse_identifier__valid_formats(data_provider, ticker_str, expected_type, expected_value):
    id_type, id_value = data_provider._parse_identifier(ticker_str)
    assert id_type == expected_type and id_value == expected_value


def test_get_history__payload_uses_specific_ticker(data_provider, es_future_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array(tickers=("ESZ1 Index",)))
    data_provider.get_history(
        tickers=es_future_ticker, fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    payload = data_provider._submit_and_download.call_args[0][0]
    identifier = payload['universe']['contains'][0]
    assert identifier['identifierValue'] == 'ESZ1 Index'


def test_get_history__output_contains_future_ticker(data_provider, es_future_ticker, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_history_array(
        tickers=("ESZ1 Index", "AAPL US Equity"), data=[[[4500.0], [150.0]]]))
    result = data_provider.get_history(
        tickers=[es_future_ticker, aapl_ticker], fields="PX_LAST",
        start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
        frequency=Frequency.DAILY, look_ahead_bias=True)
    expected = QFSeries(
        [4500.0, 150.0],
        index=pd.Index([es_future_ticker, aapl_ticker], name="tickers"),
        name="PX_LAST")
    assert_series_equal(result, expected, check_names=False)
    assert isinstance(result.index[0], BloombergFutureTicker)
    assert result.index[0].family_id == "ES{} Index"


def test_get_current_values__payload_uses_specific_ticker(data_provider, es_future_ticker):
    data_provider._submit_and_download = Mock(return_value=_current_df(tickers=("ESZ1 Index",)))
    data_provider.get_current_values(tickers=es_future_ticker, fields="PX_LAST")
    payload = data_provider._submit_and_download.call_args[0][0]
    identifier = payload['universe']['contains'][0]
    assert identifier['identifierValue'] == 'ESZ1 Index'


def test_get_current_values__output_contains_future_ticker(data_provider, es_future_ticker, aapl_ticker):
    data_provider._submit_and_download = Mock(return_value=_current_df(
        tickers=("ESZ1 Index", "AAPL US Equity"),
        data={"PX_LAST": [4500.0, 150.0]}))
    result = data_provider.get_current_values(
        tickers=[es_future_ticker, aapl_ticker], fields="PX_LAST")
    expected = QFSeries(
        [4500.0, 150.0],
        index=pd.Index([es_future_ticker, aapl_ticker]),
        name="PX_LAST")
    assert_series_equal(result, expected, check_names=False)
    assert isinstance(result.index[0], BloombergFutureTicker)
    assert result.index[0].family_id == "ES{} Index"


def test_get_futures_chain_tickers__returns_chain_with_expiration_dates(data_provider, es_future_ticker):
    active_ticker = BloombergTicker("ESA Index", SecurityType.FUTURE, 50)
    chain = [
        {"SECURITY_DES": "ESU97 Index"},
        {"SECURITY_DES": "ESZ97 Index"},
        {"SECURITY_DES": "ESH98 Index"},
    ]
    exp_df = QFDataFrame(
        data={"LAST_TRADEABLE_DT": ["1997-09-18", "1997-12-18", "1998-03-20"]},
        index=[
            BloombergTicker("ESU97 Index", SecurityType.FUTURE, 50),
            BloombergTicker("ESZ97 Index", SecurityType.FUTURE, 50),
            BloombergTicker("ESH98 Index", SecurityType.FUTURE, 50),
        ])

    def mock_get_current_values(tickers, fields, **kwargs):
        if fields == "FUT_CHAIN":
            return QFSeries(data=[chain], index=[active_ticker])
        return exp_df

    with patch.object(data_provider, 'get_current_values', side_effect=mock_get_current_values):
        result = data_provider.get_futures_chain_tickers(
            es_future_ticker, ExpirationDateField.LastTradeableDate)

    assert es_future_ticker in result
    df = result[es_future_ticker]

    expected_tickers = [
        BloombergTicker("ESU97 Index", SecurityType.FUTURE, 50),
        BloombergTicker("ESZ97 Index", SecurityType.FUTURE, 50),
        BloombergTicker("ESH98 Index", SecurityType.FUTURE, 50),
    ]
    expected_df = QFDataFrame(
        {ExpirationDateField.LastTradeableDate: ["1997-09-18", "1997-12-18", "1998-03-20"]},
        index=pd.Index(expected_tickers))
    assert_frame_equal(df, expected_df, check_names=False)

    for t in df.index:
        assert isinstance(t, BloombergTicker)
        assert t.security_type == SecurityType.FUTURE
        assert t.point_value == 50
        assert t.name == "S&P 500 E-mini"


def test_get_futures_chain_tickers__tickers_inherit_future_ticker_properties(
        data_provider, es_future_ticker):
    active_ticker = BloombergTicker("ESA Index", SecurityType.FUTURE, 50)
    chain = [{"SECURITY_DES": "ESZ97 Index"}]
    exp_df = QFDataFrame(
        data={"LAST_TRADEABLE_DT": ["1997-12-18"]},
        index=[BloombergTicker("ESZ97 Index", SecurityType.FUTURE, 50)])

    def mock_get_current_values(tickers, fields, **kwargs):
        if fields == "FUT_CHAIN":
            return QFSeries(data=[chain], index=[active_ticker])
        return exp_df

    with patch.object(data_provider, 'get_current_values', side_effect=mock_get_current_values):
        result = data_provider.get_futures_chain_tickers(
            es_future_ticker, ExpirationDateField.LastTradeableDate)

    df = result[es_future_ticker]
    specific_ticker = df.index[0]
    assert specific_ticker.name == "S&P 500 E-mini"
    assert specific_ticker.security_type == SecurityType.FUTURE
    assert specific_ticker.point_value == 50


def test__submit_and_download__session_post(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        mock_used_for__submit_and_download(data_provider, m)
        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    url = data_provider.session.post.call_args[0][0]
    assert url == "https://api.bloomberg.com/eap/catalogs/bbg0001/requests/"

    json_request_payload = data_provider.session.post.call_args.kwargs['json']

    assert json_request_payload['@type'] == 'HistoryRequest'
    assert json_request_payload['fieldList'] == {'@type': 'HistoryFieldList', 'contains': [{'mnemonic': 'PX_LAST'}]}
    assert json_request_payload['formatting'] == {'@type': 'MediaType', 'outputMediaType': 'application/json'}
    assert json_request_payload['pricingSourceOptions'] == {'@type': 'HistoryPricingSourceOptions',
                                                            'prefer': {'mnemonic': 'BGN'}}
    assert json_request_payload['runtimeOptions'] == {'@type': 'HistoryRuntimeOptions',
                                                      'dateRange': {'@type': 'IntervalDateRange',
                                                                    'endDate': '2025-06-06', 'startDate': '2025-06-06'},
                                                      'period': 'daily'}
    assert json_request_payload['trigger'] == {'@type': 'SubmitTrigger'}
    assert json_request_payload['universe'] == {'@type': 'Universe', 'contains': [
        {'@type': 'Identifier', 'identifierType': 'TICKER', 'identifierValue': 'AAPL US Equity'}]}

    data_provider.session.post.assert_called_once()


def test__submit_and_download__get_field_list_url(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        mock_used_for__submit_and_download(data_provider, m)
        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    first_get = data_provider.session.get.call_args_list[0]
    expected = f"https://api.bloomberg.com/eap/catalogs/bbg0001/requests/{RESPONSE_201_CREATED['request']['identifier']}/fieldList"
    assert first_get[0][0] == expected


def test__submit_and_download__get_download_url_contains_output_key(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        mock_used_for__submit_and_download(data_provider, m)
        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    download_url = data_provider.session.get.call_args_list[1][0][0]
    assert f"content/responses/{RESPONSE_201_CREATED['request']['identifier']}-output.bbg" in download_url


def test__submit_and_download__sse_client_tests(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        sse = mock_used_for__submit_and_download(data_provider, m)
        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    m.assert_called_once_with(
        "https://api.bloomberg.com/eap/notifications/content/responses",
        data_provider.session,
    )
    assert sse.disconnect.called


def test__submit_and_download__non_matching_event_skipped(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        sse = mock_used_for__submit_and_download(data_provider, m)
        other = _delivery_event(request_id="differentReqId")
        matching = _delivery_event()
        sse.read_event.side_effect = [other, matching]
        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    assert sse.read_event.call_count == 2
    assert data_provider.session.get.call_count == 2


def test__submit_and_download__multiple_heartbeats_then_delivery(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        sse = mock_used_for__submit_and_download(data_provider, m)
        sse.read_event.side_effect = [
            get_mock_heartbeat_event(), get_mock_heartbeat_event(), get_mock_heartbeat_event(),
            _delivery_event(),
        ]
        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    assert sse.read_event.call_count == 4


def test__submit_and_download__post_exception_handled_gracefully(data_provider, aapl_ticker):
    with patch(SSE_PATH) as m:
        sse = m.return_value
        sse.disconnect = Mock()
        post_resp = Mock(status_code=400)
        post_resp.json.return_value = RESPONSE_400_BAD_REQUEST
        data_provider.session.post.return_value = post_resp

        data_provider.get_history(tickers=aapl_ticker, fields="PX_LAST",
                                  start_date=datetime(2025, 6, 6), end_date=datetime(2025, 6, 6),
                                  frequency=Frequency.DAILY, look_ahead_bias=True)

    data_provider.session.get.assert_not_called()
    assert sse.disconnect.called
