#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS"BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import gzip
import json
from datetime import time, datetime

import numpy as np
import pandas as pd
import pytest
from numpy import float64
from numpy.testing import assert_array_almost_equal
from pandas import DataFrame
from pandas.testing import assert_frame_equal


def test_decompress_response__plain_json_bytes(parser):
    records = [{"DATE": "20250101", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 100.0}]
    result = parser.decompress_response(json.dumps(records).encode("utf-8"))
    expected = DataFrame([{"DATE": 20250101, "IDENTIFIER": "AAPL US Equity", "PX_LAST": 100.0}])
    assert_frame_equal(result, expected, check_dtype=False)


def test_decompress_response__gzipped_json_bytes(parser):
    records = [{"DATE": "20250101", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 200.0}]
    result = parser.decompress_response(gzip.compress(json.dumps(records).encode("utf-8")))
    expected = DataFrame([{"DATE": 20250101, "IDENTIFIER": "AAPL US Equity", "PX_LAST": 200.0}])
    assert_frame_equal(result, expected, check_dtype=False)


def test_decompress_response__multiple_records(parser):
    records_str = [
        {"DATE": "20250101", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 100.0},
        {"DATE": "20250102", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 101.0},
        {"DATE": "20250101", "IDENTIFIER": "MSFT", "PX_LAST": 200.0},
        {"DATE": "20250102", "IDENTIFIER": "MSFT", "PX_LAST": 201.0},
    ]
    expected = DataFrame([
        {"DATE": 20250101, "IDENTIFIER": "AAPL US Equity", "PX_LAST": 100.0},
        {"DATE": 20250102, "IDENTIFIER": "AAPL US Equity", "PX_LAST": 101.0},
        {"DATE": 20250101, "IDENTIFIER": "MSFT", "PX_LAST": 200.0},
        {"DATE": 20250102, "IDENTIFIER": "MSFT", "PX_LAST": 201.0},
    ])
    assert_frame_equal(parser.decompress_response(json.dumps(records_str).encode("utf-8")),
                       expected, check_dtype=False)


def test_decompress_response__empty_array(parser):
    result = parser.decompress_response(json.dumps([]).encode("utf-8"))
    assert_frame_equal(result, DataFrame())


def test_get_current_values__single_ticker_single_real_field(parser):
    df = DataFrame([{"IDENTIFIER": "AAPL US Equity", "PX_LAST": 150.5}])
    result = parser.get_current_values(df, {"PX_LAST": "Real"})
    expected = DataFrame({"PX_LAST": [150.5]}, index=pd.Index(["AAPL US Equity"], name="tickers"))
    assert_frame_equal(result, expected)


def test_get_current_values__multiple_tickers_multiple_fields(parser):
    df = DataFrame([
        {"IDENTIFIER": "AAPL US Equity", "PX_LAST": 150.0, "NAME": "APPLE INC"},
        {"IDENTIFIER": "MSFT", "PX_LAST": 300.0, "NAME": "MICROSOFT CORP"},
    ])
    result = parser.get_current_values(df, {"PX_LAST": "Real", "NAME": "String"})
    expected = DataFrame(
        {"PX_LAST": [150.0, 300.0], "NAME": ["APPLE INC", "MICROSOFT CORP"]},
        index=pd.Index(["AAPL US Equity", "MSFT"], name="tickers"))
    assert_frame_equal(result, expected)


def test_get_current_values__string_na_becomes_none(parser):
    df = DataFrame([{"IDENTIFIER": "HIHI Index", "NAME": "N.A."}])
    result = parser.get_current_values(df, {"NAME": "String"})
    assert result.loc["HIHI Index", "NAME"] is None


def test_get_current_values__na_real_field_becomes_nan(parser):
    df = DataFrame([{"IDENTIFIER": "HIHI Index", "VOL_90D": "N.A."}])
    result = parser.get_current_values(df, {"VOL_90D": "Real"})
    expected = DataFrame({"VOL_90D": [np.nan]}, index=pd.Index(["HIHI Index"], name="tickers"))
    assert_frame_equal(result, expected)


def test_get_current_values__date_field(parser):
    df = DataFrame([{"IDENTIFIER": "CTZ5", "FUT_NOTICE_FIRST": "2025-06-10"}])
    result = parser.get_current_values(df, {"FUT_NOTICE_FIRST": "Date"})
    expected = DataFrame(
        {"FUT_NOTICE_FIRST": pd.to_datetime(["2025-06-10"])},
        index=pd.Index(["CTZ5"], name="tickers"))
    assert_frame_equal(result, expected)


def test_get_current_values__date_field_na_becomes_none(parser):
    df = DataFrame([{"IDENTIFIER": "CTK4", "FUT_NOTICE_FIRST": "N.A."}])
    result = parser.get_current_values(df, {"FUT_NOTICE_FIRST": "Date"})
    assert result.loc["CTK4", "FUT_NOTICE_FIRST"] is None


def test_get_current_values__time_field(parser):
    df = DataFrame([{"IDENTIFIER": "Hehe Index", "ECO_RELEASE_TIME": "13:30"}])
    result = parser.get_current_values(df, {"ECO_RELEASE_TIME": "Time"})
    expected = DataFrame(
        {"ECO_RELEASE_TIME": [time(13, 30)]},
        index=pd.Index(["Hehe Index"], name="tickers"))
    assert_frame_equal(result, expected)


@pytest.mark.parametrize("field_type", ["Integer", "Price"])
def test_get_current_values__numeric_field_cast_to_float64(parser, field_type):
    df = DataFrame([{"IDENTIFIER": "AAPL US Equity", "F": 1000}])
    result = parser.get_current_values(df, {"F": field_type})
    expected = DataFrame({"F": [1000.0]}, index=pd.Index(["AAPL US Equity"], name="tickers"))
    assert_frame_equal(result, expected)


def test_get_current_values__bulk_format_list_of_dicts(parser):
    bulk_val = [
        {"SECURITY_DES": "RTYU17 Index"}, {"SECURITY_DES": "RTYZ17 Index"},
        {"SECURITY_DES": "RTYH18 Index"}, {"SECURITY_DES": "RTYM18 Index"},
        {"SECURITY_DES": "RTYU18 Index"},
    ]
    df = DataFrame([{"IDENTIFIER": "RTYA Index", "FUT_CHAIN": bulk_val}])

    result = parser.get_current_values(df, {"FUT_CHAIN": "Bulk Format"})
    assert result.loc["RTYA Index", "FUT_CHAIN"] == bulk_val


def test_get_current_values__bulk_format_empty(parser):
    df = DataFrame([{"IDENTIFIER": "Non Index", "INDEX_MEMBERS_WEIGHTS": []}])
    result = parser.get_current_values(df, {"INDEX_MEMBERS_WEIGHTS": "Bulk Format"})
    expected = DataFrame({"INDEX_MEMBERS_WEIGHTS": [[]]}, index=pd.Index(["Non Index"], name="tickers"))
    assert_frame_equal(result, expected)


def test_get_history__single_ticker_single_field(parser):
    df = DataFrame([
        {"DATE": "20250601", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 150.0},
        {"DATE": "20250602", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 151.0},
        {"DATE": "20250603", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 152.0},
    ])
    result = parser.get_history(df, {"PX_LAST": "Real"})
    assert_array_almost_equal(result.values.flatten(), [150.0, 151.0, 152.0])
    assert list(result.tickers.values) == ["AAPL US Equity"]
    assert list(result.fields.values) == ["PX_LAST"]


def test_get_history__multiple_tickers_multiple_fields(parser):
    df = DataFrame([
        {"DATE": "20250601", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 150.0, "PX_OPEN": 149.0},
        {"DATE": "20250601", "IDENTIFIER": "MSFT", "PX_LAST": 300.0, "PX_OPEN": 299.0},
        {"DATE": "20250602", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 151.0, "PX_OPEN": 150.0},
        {"DATE": "20250602", "IDENTIFIER": "MSFT", "PX_LAST": 301.0, "PX_OPEN": 300.0},
        {"DATE": "20250603", "IDENTIFIER": "AAPL US Equity", "PX_LAST": 152.0, "PX_OPEN": 151.0},
        {"DATE": "20250603", "IDENTIFIER": "MSFT", "PX_LAST": 302.0, "PX_OPEN": 301.0},
    ])
    result = parser.get_history(df, {"PX_LAST": "Real", "PX_OPEN": "Real"})
    assert_array_almost_equal(result.sel(tickers="AAPL US Equity", fields="PX_LAST").values, [150.0, 151.0, 152.0])
    assert_array_almost_equal(result.sel(tickers="MSFT", fields="PX_OPEN").values, [299.0, 300.0, 301.0])
    assert list(result.tickers.values) == ["AAPL US Equity", "MSFT"]
    assert list(result.fields.values) == ["PX_LAST", "PX_OPEN"]

def test_get_history__date_field_in_history(parser):
    df = DataFrame([
        {"DATE": "20250601", "IDENTIFIER": "CTZ5", "FUT_NOTICE_FIRST": "2025-09-15", "PX_LAST": 100.0},
    ])
    result = parser.get_history(df, {"FUT_NOTICE_FIRST": "Date", "PX_LAST": "Real"})
    val = result.sel(tickers="CTZ5", fields="FUT_NOTICE_FIRST").values[0]
    assert val.to_pydatetime() == datetime(2025, 9, 15)
    assert float(result.sel(tickers="CTZ5", fields="PX_LAST").values[0]) == 100.0


def test_get_history__nan_values_preserved(parser):
    df = DataFrame([{"DATE": "20250601", "IDENTIFIER": "AAPL US Equity", "PX_LAST": np.nan}])
    result = parser.get_history(df, {"PX_LAST": "Real"})
    assert np.isnan(float(result.sel(tickers="AAPL US Equity", fields="PX_LAST").values[0]))


def test_get_history__na_string_replaced_with_none_or_nan(parser):
    df = DataFrame([
        {"DATE": "20250601", "IDENTIFIER": "ESZ7 Index", "RATING": "N.A.", "PX_LAST": 100.0, "PX_OPEN": "N.A."},
    ])
    result = parser.get_history(df, {"RATING": "String", "PX_LAST": "Real", "PX_OPEN": "Real"})
    rating_val = result.sel(tickers="ESZ7 Index", fields="RATING").values[0]
    assert rating_val is None
    px_open = result.sel(tickers="ESZ7 Index", fields="PX_OPEN").values[0]
    assert (isinstance(px_open, float) and np.isnan(px_open))
    assert float(result.sel(tickers="ESZ7 Index", fields="PX_LAST").values[0]) == 100.0
