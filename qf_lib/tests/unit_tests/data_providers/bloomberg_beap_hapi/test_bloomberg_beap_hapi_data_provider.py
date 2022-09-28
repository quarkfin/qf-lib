from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, Mock

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider import BloombergBeapHapiDataProvider


class TestBloombergBeapHapiDataProvider(TestCase):

    def setUp(self) -> None:
        def __init__(_self, _):
            _self.fields_hapi_provider = Mock()
            _self.fields_hapi_provider.get_fields_url.return_value = Mock(), Mock()
            _self.universe_hapi_provider = Mock()
            _self.request_hapi_provider = Mock()
            _self.parser = Mock()
            _self.connected = True
            _self.reply_timeout = timedelta(minutes=0)
            _self.logger = Mock()
            _self.sse_client = Mock()

        beap_hapi_patcher = patch.object(BloombergBeapHapiDataProvider, '__init__', __init__)
        beap_hapi_patcher.start()
        self.addCleanup(beap_hapi_patcher.stop)

        self.data_provider = BloombergBeapHapiDataProvider(Mock())

    def test_get_tickers_universe__invalid_date(self):
        with self.assertRaises(ValueError):
            self.data_provider.get_tickers_universe(BloombergTicker("Example Index"), datetime(1970, 1, 1))

    def test_get_tickers_universe__valid_ticker(self):
        self.data_provider.parser.get_current_values.return_value = QFDataFrame.from_records(
            [("SPX Index", ["Member1", "Member2"]), ], columns=["Ticker", "INDX_MEMBERS"]).set_index("Ticker")

        universe = self.data_provider.get_tickers_universe(BloombergTicker("SPX Index"))
        self.assertCountEqual(universe, [BloombergTicker("Member1 Equity"), BloombergTicker("Member2 Equity")])

    def test_get_tickers_universe__invalid_ticker(self):
        self.data_provider.parser.get_current_values.return_value = QFDataFrame.from_records(
            [("Invalid Index", []), ], columns=["Ticker", "INDX_MEMBERS"]).set_index("Ticker")

        universe = self.data_provider.get_tickers_universe(BloombergTicker("Invalid Index"))
        self.assertCountEqual(universe, [])
