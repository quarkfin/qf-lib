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
from unittest import TestCase, skipIf
from unittest.mock import Mock

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.series.qf_series import QFSeries

try:
    from qf_lib.brokers.ib_broker.ib_contract import IBContract
    from qf_lib.backtesting.contract.contract_to_ticker_conversion.ib_contract_ticker_mapper import \
        IBContractTickerMapper
    is_ibapi_installed = True
except ImportError:
    is_ibapi_installed = False


@skipIf(not is_ibapi_installed, "No Interactive Brokers API installed. Tests are being skipped.")
class TestIBContractTickerMapper(TestCase):
    def setUp(self) -> None:
        self.data_provider = Mock()
        self.data_provider.get_futures_chain_tickers.side_effect = lambda t, _: {
            t: QFSeries(index=[BloombergTicker("HGH20 Comdty", SecurityType.FUTURE, 250),
                               BloombergTicker("HGN20 Comdty", SecurityType.FUTURE, 250)],
                        data=[str_to_date("2020-03-20"), str_to_date("2020-06-20")])
        }

    def test_futures_contract_to_ticker_mapping(self):
        """ Test contract to ticker mapping, in case of a futures contract when the mapping between a specific futures
        ticker and an IBContract was provided. """
        mapping = {
            BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100):
                IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping)
        contract = IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
        actual_ticker = contract_ticker_mapper.contract_to_ticker(contract)

        expected_ticker = BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100)
        self.assertEqual(actual_ticker, expected_ticker)

    def test_ticker_to_futures_contract_mapping(self):
        """ Test contract to ticker mapping, in case of a futures contract when the mapping between a specific futures
                ticker and an IBContract was provided. """
        mapping = {
            BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100):
                IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping)
        ticker = BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100)
        actual_contract = contract_ticker_mapper.ticker_to_contract(ticker)

        expected_contract = IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
        self.assertEqual(expected_contract, actual_contract)

    def test_contract_to_ticker_no_valid_mapping(self):
        """ Test contract to ticker mapping if no mapping for the ticker exists. """
        contract_ticker_mapper = IBContractTickerMapper({})
        contract = IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
        with self.assertRaises(ValueError):
            contract_ticker_mapper.contract_to_ticker(contract)

    def test_ticker_to_contract_no_valid_mapping(self):
        """ Test ticker to contract mapping if no mapping for the ticker exists. """
        contract_ticker_mapper = IBContractTickerMapper({})
        ticker = BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100)
        with self.assertRaises(ValueError):
            contract_ticker_mapper.ticker_to_contract(ticker)

    def test_futures_contract_to_ticker_invalid_last_trade_date(self):
        """ Test contract to ticker mapping, in case if the last trade date in the IBContract is invalid. """
        mapping = {
            BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100):
                IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping)
        contract = IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-10"))

        with self.assertRaises(ValueError):
            contract_ticker_mapper.contract_to_ticker(contract)

    def test_future_ticker_to_contract_mapping(self):
        """ Test mapping of future tickers onto IB contracts. """
        mapping = {
            BloombergFutureTicker('Copper', 'HG{} Comdty', 1, 1, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD"),
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping, self.data_provider)

        # Map a specific ticker to contract
        ticker = BloombergTicker("HGH20 Comdty", SecurityType.FUTURE, 250)
        actual_contract = contract_ticker_mapper.ticker_to_contract(ticker)
        expected_contract = IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD", str_to_date("2020-03-20"))
        self.assertEqual(actual_contract, expected_contract)

        # Map a future ticker to contract
        future_ticker = Mock(spec=BloombergFutureTicker)
        future_ticker.get_current_specific_ticker.return_value = BloombergTicker("HGN20 Comdty", SecurityType.FUTURE,
                                                                                 250)
        actual_contract = contract_ticker_mapper.ticker_to_contract(future_ticker)
        expected_contract = IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD", str_to_date("2020-06-20"))
        self.assertEqual(actual_contract, expected_contract)

    def test_contract_to_specific_future_ticker_mapping(self):
        mapping = {
            BloombergFutureTicker('Copper', 'HG{} Comdty', 1, 1, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD"),
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping, self.data_provider)
        contract = IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD", str_to_date("2020-06-20"))
        actual_ticker = contract_ticker_mapper.contract_to_ticker(contract)
        expected_ticker = BloombergTicker("HGN20 Comdty", SecurityType.FUTURE, 250)
        self.assertEqual(actual_ticker, expected_ticker)

    def test_invalid_contract_to_specific_future_ticker_mapping(self):
        """ Test futures contract to ticker mapping in case if the last trade date is invalid. """
        mapping = {
            BloombergFutureTicker('Copper', 'HG{} Comdty', 1, 1, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD"),
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping, self.data_provider)
        contract = IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD", str_to_date("2020-06-25"))
        with self.assertRaises(ValueError):
            contract_ticker_mapper.contract_to_ticker(contract)

    def test_contract_ticker_mapping_many_future_tickers(self):
        """ Test futures contract to ticker mapping in case if many future tickers correspond to the given ticker. """
        mapping = {
            BloombergFutureTicker('Copper', 'HG{} Comdty', 1, 1, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD"),
            BloombergFutureTicker('Copper', 'HG{} Comdty', 1, 17, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "250", "USD"),
        }
        contract_ticker_mapper = IBContractTickerMapper(mapping, self.data_provider)

        with self.assertRaises(ValueError):
            ticker = BloombergTicker("HGH20 Comdty", SecurityType.FUTURE, 250)
            contract_ticker_mapper.ticker_to_contract(ticker)

    def test_contract_ticker_mapping_multiple_tickers_matching_contract(self):
        """ Test  contract to ticker mapping in case if many tickers correspond to the same contract. """
        mapping = {
            BloombergFutureTicker('Copper1', 'HG{} Comdty', 1, 1, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD"),
            BloombergFutureTicker('Copper2', 'HG{} Comdty', 1, 2, 250):
                IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD"),
        }

        with self.assertRaises(AssertionError):
            IBContractTickerMapper(mapping, self.data_provider)

    def test_no_data_provider(self):
        fut_ticker = BloombergFutureTicker("Copper", "HG{} Comdty", 1, 4)

        bbg_ib_symbols_mapping = {fut_ticker: IBContract("HG",  SecurityType.FUTURE, "NYMEX", "25000")}
        with self.assertRaises(ValueError):
            contract_ticker_mapper = IBContractTickerMapper(bbg_ib_symbols_mapping, data_provider=None)
            contract_ticker_mapper.contract_to_ticker(IBContract("HG",  SecurityType.FUTURE, "NYMEX", "25000",
                                                                 last_trade_date=datetime(2021, 9, 9)))

    def test_duplicate_future_tickers(self):
        future_ticker_1 = BloombergFutureTicker("Copper", "HG{} Comdty", 1, 4)
        future_ticker_2 = BloombergFutureTicker("Example", "Example{} Comdty", 1, 4)

        bbg_ib_symbols_mapping = {
            future_ticker_1: IBContract("EXAMPLE", SecurityType.FUTURE, "DIFFERENT_EXCHANGE", "25000"),
            future_ticker_2: IBContract("EXAMPLE", SecurityType.FUTURE, "EXAMPLE_EXCHANGE", "25000"),
        }

        with self.assertRaises(Exception):
            IBContractTickerMapper(bbg_ib_symbols_mapping, self.data_provider)

    def test_duplicate_future_and_equity_tickers(self):
        future_ticker_1 = BloombergFutureTicker("Copper", "HG{} Comdty", 1, 4)

        bbg_ib_symbols_mapping = {
            future_ticker_1: IBContract("EXAMPLE", SecurityType.FUTURE, "DIFFERENT_EXCHANGE", "25000"),
            BloombergTicker("Example Index"): IBContract("EXAMPLE", SecurityType.STOCK, "EXAMPLE_EXCHANGE"),
        }

        contract_ticker_mapper = IBContractTickerMapper(bbg_ib_symbols_mapping, self.data_provider)
        contract = IBContract("EXAMPLE", SecurityType.STOCK, "EXAMPLE_EXCHANGE")
        ticker = contract_ticker_mapper.contract_to_ticker(contract)
        self.assertEqual(ticker.as_string(), "Example Index")

    def test_duplicate_stock_tickers(self):
        bbg_ib_symbols_mapping = {
            BloombergTicker("Example Index"): IBContract("EXAMPLE", SecurityType.STOCK, "EXAMPLE_EXCHANGE"),
            BloombergTicker("Example 2 Index"): IBContract("EXAMPLE", SecurityType.STOCK, "EXAMPLE_EXCHANGE"),
        }

        with self.assertRaises(Exception):
            IBContractTickerMapper(bbg_ib_symbols_mapping)
