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

import os
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.adanos import AdanosDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal, assert_series_equal


class TestAdanosDataProvider(TestCase):

    def setUp(self):
        self.provider = AdanosDataProvider(api_key="test-key")
        self.start_date = datetime(2026, 5, 1)
        self.end_date = datetime(2026, 5, 3)

    def test_get_history_returns_daily_sentiment_series(self):
        payload = {
            "ticker": "AAPL",
            "found": True,
            "daily_trend": [
                {"date": "2026-05-01", "sentiment_score": 0.1, "buzz_score": 20.0, "mentions": 4},
                {"date": "2026-05-02", "sentiment_score": 0.2, "buzz_score": 25.0, "mentions": 6},
            ],
        }

        with patch.object(self.provider, "_request_json", return_value=payload) as request_json:
            result = self.provider.get_history(
                BloombergTicker("AAPL US Equity"),
                "sentiment_score",
                self.start_date,
                self.end_date,
            )

        request_json.assert_called_once_with(
            "/reddit/stocks/v1/stock/AAPL",
            {"from": "2026-05-01", "to": "2026-05-03"},
        )
        expected = QFSeries([0.1, 0.2], index=[datetime(2026, 5, 1), datetime(2026, 5, 2)])
        expected.name = "AAPL US Equity"
        expected.index.name = "dates"
        assert_series_equal(result, expected)

    def test_get_history_supports_multiple_tickers_and_fields(self):
        tickers = [BloombergTicker("AAPL US Equity"), BloombergTicker("MSFT US Equity")]
        payloads = [
            {
                "ticker": "AAPL",
                "found": True,
                "sentiment_score": 0.1,
                "buzz_score": 20.0,
                "mentions": 4,
            },
            {
                "ticker": "MSFT",
                "found": True,
                "sentiment_score": -0.2,
                "buzz_score": 15.0,
                "mentions": 5,
            },
        ]

        with patch.object(self.provider, "_request_json", side_effect=payloads):
            result = self.provider.get_history(
                tickers,
                ["sentiment_score", "mentions"],
                self.end_date,
                self.end_date,
            )

        expected = QFDataFrame(
            [[0.1, 4], [-0.2, 5]],
            index=tickers,
            columns=["sentiment_score", "mentions"],
        )
        expected.index.name = "tickers"
        expected.columns.name = "fields"
        assert_dataframes_equal(result, expected)

    def test_get_history_rejects_non_daily_frequency(self):
        with self.assertRaisesRegex(ValueError, "daily sentiment data only"):
            self.provider.get_history(
                BloombergTicker("AAPL US Equity"),
                "sentiment_score",
                self.start_date,
                self.end_date,
                frequency=Frequency.WEEKLY,
            )

    def test_get_history_uses_selected_source(self):
        provider = AdanosDataProvider(api_key="test-key", source="x")
        payload = {"ticker": "AAPL", "found": True, "sentiment_score": 0.1}

        with patch.object(provider, "_request_json", return_value=payload) as request_json:
            provider.get_history(
                BloombergTicker("AAPL US Equity"),
                "sentiment_score",
                self.end_date,
                self.end_date,
            )

        request_json.assert_called_once_with(
            "/x/stocks/v1/stock/AAPL",
            {"from": "2026-05-03", "to": "2026-05-03"},
        )

    def test_get_history_rejects_non_stock_ticker(self):
        with self.assertRaisesRegex(ValueError, "stock tickers only"):
            self.provider.get_history(
                BloombergTicker("BTC US Equity", security_type=SecurityType.CRYPTO),
                "sentiment_score",
                self.start_date,
                self.end_date,
            )

    def test_missing_api_key_raises_clear_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "api_key or ADANOS_API_KEY"):
                AdanosDataProvider()
