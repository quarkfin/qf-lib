import unittest
from unittest import TestCase

from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.execution_handler.simulated.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.execution_handler.simulated.slippage.volume_based_slippage import VolumeBasedSlippage
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.testing_tools.containers_comparison import assert_lists_equal


class TestSlippage(TestCase):
    def setUp(self):
        msft_ticker = BloombergTicker("MSFT US Equity")
        aapl_ticker = BloombergTicker("AAPL US Equity")
        googl_ticker = BloombergTicker("GOOGL US Equity")

        self.tickers = [
            msft_ticker, aapl_ticker, googl_ticker
        ]

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

    def test_price_based_slippage(self):
        slippage_model = PriceBasedSlippage(slippage_rate=0.1)

        actual_fill_prices, actual_fill_volumes = slippage_model.apply_slippage(
            self.orders, self.prices_without_slippage
        )
        expected_fill_prices = [1.1, 90.0, 1100.0]
        expected_fill_volumes = [1000, -10, 1]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)


if __name__ == '__main__':
    unittest.main()
