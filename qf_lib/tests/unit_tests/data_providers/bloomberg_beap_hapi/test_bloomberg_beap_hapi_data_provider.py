from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, Mock

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider import BloombergBeapHapiDataProvider


class TestBloombergBeapHapiDataProvider(TestCase):

    def setUp(self) -> None:
        def __init__(_self, _):
            field_to_type = {
                "PX_LAST": "float"
            }
            _self.fields_hapi_provider = Mock()
            _self.fields_hapi_provider.get_fields_history_url.return_value = (Mock(), field_to_type)
            _self.fields_hapi_provider.get_fields_url.return_value = (Mock(), Mock())
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
        self.data_provider.timer = SettableTimer(datetime(2025, 2, 10))

    def test_get_tickers_universe__invalid_date(self):
        with self.assertRaises(ValueError):
            self.data_provider.get_tickers_universe(BloombergTicker("Example Index"), datetime(1970, 1, 1))

    def test_get_tickers_universe__valid_ticker(self):
        self.data_provider.parser.get_current_values.return_value = QFDataFrame.from_records(
            [(BloombergTicker("SPX Index"), ["Member1", "Member2"]), ],
            columns=["Ticker", "INDEX_MEMBERS_WEIGHTS"]).set_index("Ticker")

        universe = self.data_provider.get_tickers_universe(BloombergTicker("SPX Index"))
        self.assertCountEqual(universe, [BloombergTicker("Member1 Equity"), BloombergTicker("Member2 Equity")])

    def test_get_tickers_universe__invalid_ticker(self):
        self.data_provider.parser.get_current_values.return_value = QFDataFrame.from_records(
            [(BloombergTicker("Invalid Index"), []), ], columns=["Ticker", "INDEX_MEMBERS_WEIGHTS"]).set_index("Ticker")

        universe = self.data_provider.get_tickers_universe(BloombergTicker("Invalid Index"))
        self.assertCountEqual(universe, [])

    """ Test get_history for SettableTimer """

    def test_get_history__single_field_single_ticker_single_date_daily(self):
        ticker = BloombergTicker("AAPL US Equity")
        dates = [datetime(2025, 2, 7)]
        data = [[[100.0]]]
        self.data_provider.parser.get_history.return_value = QFDataArray.create(data=data, dates=dates,
                                                                                tickers=[ticker], fields=["PX_LAST"])
        result = self.data_provider.get_history(tickers=ticker, fields="PX_LAST", start_date=datetime(2025, 2, 7),
                                                end_date=datetime(2025, 2, 7), frequency=Frequency.DAILY,
                                                look_ahead_bias=True)
        expected_result = 100.0
        self.assertEqual(result, expected_result)

    def test_get_history__single_field_single_ticker_multiple_dates_daily(self):
        ticker = BloombergTicker("AAPL US Equity")
        dates = [datetime(2025, 2, 6), datetime(2025, 2, 7)]
        data = [[[100.0]], [[101.0]]]
        self.data_provider.parser.get_history.return_value = QFDataArray.create(data=data, dates=dates,
                                                                                tickers=[ticker], fields=["PX_LAST"])
        result = self.data_provider.get_history(tickers=ticker, fields="PX_LAST", start_date=datetime(2025, 2, 6),
                                                end_date=datetime(2025, 2, 7), frequency=Frequency.DAILY,
                                                look_ahead_bias=True)
        expected_result = QFSeries([100.0, 101.0], index=dates)
        self.assertTrue(result.equals(expected_result))

    def test_get_history__multiple_fields_multiple_tickers_multiple_dates_daily(self):
        tickers = [BloombergTicker("AAPL US Equity"), BloombergTicker("MSFT US Equity")]
        dates = [datetime(2025, 2, 6), datetime(2025, 2, 7)]
        data = [[[100.0, 101.0], [200.0, 201.0]], [[5000, 5200], [10000, 10200]]]
        data_array = QFDataArray.create(data=data, dates=dates, tickers=tickers, fields=["PX_LAST", "VOLUME"])
        self.data_provider.parser.get_history.return_value = data_array
        result = self.data_provider.get_history(tickers=tickers, fields=["PX_LAST", "VOLUME"],
                                                start_date=datetime(2025, 2, 6), end_date=datetime(2025, 2, 7),
                                                frequency=Frequency.DAILY, look_ahead_bias=True)
        self.assertTrue(result.equals(data_array))
