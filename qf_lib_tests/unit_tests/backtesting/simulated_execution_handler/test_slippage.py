import unittest
from unittest import TestCase

import pandas as pd

from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.execution_handler.simulated.slippage.fixed_slippage import FixedSlippage
from qf_lib.backtesting.execution_handler.simulated.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.execution_handler.simulated.slippage.volume_share_slippage import VolumeShareSlippage
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dimension_names import TICKERS, FIELDS
from qf_lib.testing_tools.containers_comparison import assert_lists_equal


class TestSlippage(TestCase):
    def setUp(self):
        msft_ticker = BloombergTicker("MSFT US Equity")
        aapl_ticker = BloombergTicker("AAPL US Equity")
        googl_ticker = BloombergTicker("GOOGL US Equity")

        self.tickers = [
            msft_ticker, aapl_ticker, googl_ticker
        ]

        self.data_handler = self._create_data_handler_mock()

        self.contract_ticker_mapper = DummyBloombergContractTickerMapper()

        self.orders = [
            Order(
                contract=self.contract_ticker_mapper.ticker_to_contract(msft_ticker),
                quantity=1000,
                execution_style=MarketOrder(),
                time_in_force=TimeInForce.GTC
            ),
            Order(
                contract=self.contract_ticker_mapper.ticker_to_contract(aapl_ticker),
                quantity=-10,
                execution_style=MarketOrder(),
                time_in_force=TimeInForce.GTC
            ),
            Order(
                contract=self.contract_ticker_mapper.ticker_to_contract(googl_ticker),
                quantity=1,
                execution_style=MarketOrder(),
                time_in_force=TimeInForce.GTC
            )
        ]
        self.prices_without_slippage = [1.0, 100.0, 1000.0]

    def _create_data_handler_mock(self):
        saved_tickers = self.tickers

        class DataHandlerMock(object):
            def get_bar_for_today(self, tickers):
                assert set(tickers) == set(saved_tickers)

                result = pd.DataFrame(
                    index=pd.Index(saved_tickers, name=TICKERS),
                    columns=pd.Index([
                        PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume
                    ], name=FIELDS),
                    data=[
                        [1.0, 2.0, 3.0, 4.0, 5.0],       # MSFT
                        [6.0, 7.0, 8.0, 9.0, 10.0],      # AAPL
                        [11.0, 12.0, 13.0, 14.0, 100.0]  # GOOGL
                    ]
                )

                return result

        data_handler = DataHandlerMock()  # type: DataHandler

        return data_handler

    def test_price_based_slippage(self):
        slippage_model = PriceBasedSlippage(slippage_rate=0.1)

        actual_fill_prices, actual_fill_volumes = slippage_model.apply_slippage(
            self.orders, self.prices_without_slippage
        )
        expected_fill_prices = [1.1, 90.0, 1100.0]
        expected_fill_volumes = [1000, -10, 1]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_volume_share_slippage(self):
        slippage_model = VolumeShareSlippage(volume_share_limit=0.1, price_impact=0.1, data_handler=self.data_handler,
                                             contract_ticker_mapper=DummyBloombergContractTickerMapper())

        actual_fill_prices, actual_fill_volumes = slippage_model.apply_slippage(
            self.orders, self.prices_without_slippage
        )

        expected_fill_prices = [float("nan"), 99.9, 1000.01]
        expected_fill_volumes = [0, -1, 1]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_fixed_slippage(self):
        slippage_model = FixedSlippage(slippage_per_share=0.05)

        actual_fill_prices, actual_fill_volumes = slippage_model.apply_slippage(
            self.orders, self.prices_without_slippage
        )

        expected_fill_prices = [1.05, 99.95, 1000.05]
        expected_fill_volumes = [1000, -10, 1]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)


if __name__ == '__main__':
    unittest.main()
