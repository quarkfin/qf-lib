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
from unittest import TestCase

from qf_lib.backtesting.contract.contract_to_ticker_conversion.bbg_figi_mapper import BloombergTickerMapper
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker


class TestBloombergTickerMapper(TestCase):

    def test_ticker_to_figi__no_data_preloading(self):
        mapper = BloombergTickerMapper(data_caching=False)

        tickers = [BloombergTicker("SPX Index", SecurityType.INDEX),
                   BloombergTicker("SPY US Equity", SecurityType.STOCK),
                   BloombergTicker("USDCHF Curncy", SecurityType.FX)]
        expected_figis = ["BBG000H4FSM0", "BBG000BDTBL9", "BBG0013HFN45"]

        for ticker, figi in zip(tickers, expected_figis):
            with self.subTest(f"Testing {ticker} to FIGI mapping."):
                self.assertEqual(mapper.ticker_to_contract(ticker), figi)

    def test_incorrect_ticker_to_figi__no_data_preloading(self):
        mapper = BloombergTickerMapper(data_caching=False)

        tickers = [BloombergTicker("Incorrect Index", SecurityType.INDEX),
                   BloombergTicker("Hihihi", SecurityType.STOCK)]

        for ticker in tickers:
            with self.subTest(f"Testing {ticker} to FIGI mapping."):
                self.assertIsNone(mapper.ticker_to_contract(ticker))

    def test_incorrect_figi_to_ticker__no_data_preloading(self):
        mapper = BloombergTickerMapper(data_caching=False)
        figi = "HIHIHIHIHI"
        self.assertIsNone(mapper.contract_to_ticker(figi))

    def test_figi_to_ticker__no_data_preloading(self):
        mapper = BloombergTickerMapper(data_caching=False)

        figis = ["BBG000H4FSM0", "BBG000BDTBL9", "BBG0013HFN45"]
        expected_tickers = [BloombergTicker("SPX Index", SecurityType.INDEX),
                            BloombergTicker("SPY US Equity", SecurityType.STOCK),
                            BloombergTicker("USDCHF Curncy", SecurityType.FX)]

        for figi, ticker in zip(figis, expected_tickers):
            with self.subTest(f"Testing {figi} to Bloomberg Ticker mapping."):
                self.assertEqual(mapper.contract_to_ticker(figi), ticker)

    def test_ticker_to_figi__with_data_preloading(self):
        mapper = BloombergTickerMapper(data_caching=True)
        tickers = [BloombergTicker("SPX Index", SecurityType.INDEX),
                   BloombergTicker("SPY US Equity", SecurityType.STOCK),
                   BloombergTicker("USDCHF Curncy", SecurityType.FX)]
        mapper.preload_tickers_mapping(tickers)

        expected_figis = ["BBG000H4FSM0", "BBG000BDTBL9", "BBG0013HFN45"]

        for ticker, figi in zip(tickers, expected_figis):
            with self.subTest(f"Testing {ticker} to FIGI mapping."):
                self.assertEqual(mapper.ticker_to_contract_data[ticker], figi)

    def test_figi_to_ticker__with_data_preloading(self):
        mapper = BloombergTickerMapper(data_caching=True)
        figis = ["BBG000H4FSM0", "BBG000BDTBL9", "BBG0013HFN45"]
        mapper.preload_figi_mapping(figis)

        expected_tickers = [BloombergTicker("SPX Index", SecurityType.INDEX),
                            BloombergTicker("SPY US Equity", SecurityType.STOCK),
                            BloombergTicker("USDCHF Curncy", SecurityType.FX)]

        for figi, ticker in zip(figis, expected_tickers):
            with self.subTest(f"Testing {figi} to Bloomberg Ticker mapping."):
                self.assertEqual(mapper.contract_data_to_ticker[figi], ticker)
