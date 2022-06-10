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
import math
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, Mock

import pandas as pd
import numpy as np

from qf_lib.backtesting.execution_handler.slippage.fixed_slippage import FixedSlippage
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.execution_handler.slippage.square_root_market_impact_slippage import SquareRootMarketImpactSlippage
from qf_lib.backtesting.order.execution_style import MarketOrder, MarketOnCloseOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dimension_names import TICKERS, FIELDS
from qf_lib.data_providers.helpers import tickers_dict_to_data_array, normalize_data_array
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class TestSlippage(TestCase):
    def setUp(self):
        msft_ticker = BloombergTicker("MSFT US Equity")
        aapl_ticker = BloombergTicker("AAPL US Equity")
        googl_ticker = BloombergTicker("GOOGL US Equity")

        self.tickers = [msft_ticker, aapl_ticker, googl_ticker]
        self.data_provider = self._create_data_provider_mock()

        self.orders = [
            Order(
                ticker=msft_ticker,
                quantity=1250,
                execution_style=MarketOrder(),
                time_in_force=TimeInForce.GTC
            ),
            Order(
                ticker=aapl_ticker,
                quantity=-200,
                execution_style=MarketOrder(),
                time_in_force=TimeInForce.GTC
            ),
            Order(
                ticker=googl_ticker,
                quantity=1,
                execution_style=MarketOrder(),
                time_in_force=TimeInForce.GTC
            )
        ]

        self.market_on_close_order = [Order(
                ticker=msft_ticker,
                quantity=1250,
                execution_style=MarketOnCloseOrder(),
                time_in_force=TimeInForce.GTC
            )]

    def _create_data_provider_mock(self):
        def get_price(tickers, fields, start_date, end_date, _):
            prices_bar = [5.0, 10.0, 1.0, 4.0, 50]  # Open, High, Low, Close, Volume

            dates_index = pd.date_range(start_date, end_date, freq='B')
            tickers, got_single_ticker = convert_to_list(tickers, Ticker)
            fields, got_single_field = convert_to_list(fields, PriceField)
            got_single_date = len(dates_index) == 1

            prices_df = pd.DataFrame(
                index=pd.Index(dates_index, name=TICKERS),
                columns=pd.Index(PriceField.ohlcv(), name=FIELDS),
                data=[prices_bar] * len(dates_index)
            )
            data_array = tickers_dict_to_data_array({
                ticker: prices_df for ticker in self.tickers
            }, self.tickers, PriceField.ohlcv())

            return normalize_data_array(data_array.loc[start_date:end_date, tickers, fields], tickers, fields,
                                        got_single_date, got_single_ticker, got_single_field)

        data_provider = MagicMock()
        data_provider.get_price.side_effect = get_price

        return data_provider

    def test_price_based_slippage__no_volume_limits(self):
        """Volume should remain the same. Prices should be increased by the slippage rate."""
        slippage_rate = 0.1
        slippage_model = PriceBasedSlippage(slippage_rate, self.data_provider)

        prices_without_slippage = [20.0, 30.0, 40.0]
        # Each price should be changed by +0.1 / -0.1 depending on whether it is a BUY or SELL
        expected_fill_prices = [22.0, 27.0, 44.0]

        # Volumes should remain equal to the initial quantities
        expected_fill_volumes = [order.quantity for order in self.orders]  # [1250, -200, 1]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_price_based_slippage__with_volume(self):
        """Volume should be changed in case of exceeding limits. Slippage rate is set to 0.0, so the prices should
        remain unchanged."""
        slippage_rate = 0.0
        max_volume_share_limit = 0.1
        slippage_model = PriceBasedSlippage(slippage_rate, self.data_provider, max_volume_share_limit)

        prices_without_slippage = [20.0, 30.0, 40.0]
        expected_fill_prices = prices_without_slippage

        # Mean historical volume is set to 50.0 for each of the tickers. As the max_volume_share_limit = 0.1, the limit
        # is set to +/-5.0
        expected_fill_volumes = [5.0, -5.0, 1]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_price_based_slippage__nan_prices(self):
        slippage_rate = 0.1
        slippage_model = PriceBasedSlippage(slippage_rate, self.data_provider)

        prices_without_slippage = [float('nan'), np.nan, float('nan')]
        expected_fill_prices = [float('nan'), float('nan'), float('nan')]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)
        assert_lists_equal(expected_fill_prices, actual_fill_prices)

    def test_fixed_slippage__no_volume(self):
        """Volume should remain unchanged. Prices should be increased by the slippage rate."""
        slippage_per_share = 0.05
        slippage_model = FixedSlippage(slippage_per_share=slippage_per_share, data_provider=self.data_provider)

        prices_without_slippage = [20.0, 30.0, 40.0]
        # [BUY, SELL, BUY] => [+, -, +]
        expected_fill_prices = [20.0 + slippage_per_share, 30.0 - slippage_per_share, 40.0 + slippage_per_share]

        # Volumes should remain equal to the initial quantities
        expected_fill_volumes = [order.quantity for order in self.orders]  # [1250, -200, 1]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_fixed_slippage__with_volume(self):
        """Prices should remain unchanged."""
        slippage_per_share = 0.0
        max_volume_share_limit = 0.1
        slippage_model = FixedSlippage(slippage_per_share=slippage_per_share, data_provider=self.data_provider,
                                       max_volume_share_limit=max_volume_share_limit)

        prices_without_slippage = [20.0, 30.0, 40.0]
        expected_fill_prices = prices_without_slippage

        # Mean historical volume is set to 50.0 for each of the tickers.
        expected_fill_volumes = [5.0, -5.0, 1]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_fixed_slippage__nan_prices(self):
        slippage_per_share = 0.1
        slippage_model = FixedSlippage(slippage_per_share, self.data_provider)

        prices_without_slippage = [float('nan'), np.nan, float('nan')]
        expected_fill_prices = [float('nan'), float('nan'), float('nan')]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)
        assert_lists_equal(expected_fill_prices, actual_fill_prices)

    def test_square_root_market_slippage__no_volume(self):
        """The volatility used by the slippage model is mocked to be equal to 0.1. The volume is equal to 50.0"""
        price_impact = 0.1
        close_prices_volatility = 0.1
        prices_without_slippage = [20.0, 30.0, 40.0]

        slippage_model = SquareRootMarketImpactSlippage(price_impact=price_impact,
                                                        data_provider=self.data_provider)

        slippage_model._compute_volatility = Mock()
        slippage_model._compute_volatility.return_value = close_prices_volatility

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date('2020-01-01'),
                                                                                self.orders,
                                                                                prices_without_slippage)

        expected_fill_prices = [20.0 + 20.0 * price_impact * close_prices_volatility * math.sqrt(1250 / 50.0),
                                30.0 - 30.0 * price_impact * close_prices_volatility * math.sqrt(200 / 50.0),
                                40.0 + 40.0 * price_impact * close_prices_volatility * math.sqrt(1 / 50.0)]

        # Volumes should remain equal to the initial quantities
        expected_fill_volumes = [order.quantity for order in self.orders]  # [1250, -200, 1]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_square_root_market_slippage__no_volume_no_volatility(self):
        """As all the mocked close prices are equal, the volatility should be equal to 0.0. Thus, the prices do not
        change after applying slippage."""
        price_impact = 0.1
        prices_without_slippage = [20.0, 30.0, 40.0]

        slippage_model = SquareRootMarketImpactSlippage(price_impact=price_impact,
                                                        data_provider=self.data_provider)

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date('2020-01-01'),
                                                                                self.orders,
                                                                                prices_without_slippage)

        expected_fill_prices = prices_without_slippage

        # Volumes should remain equal to the initial quantities
        expected_fill_volumes = [order.quantity for order in self.orders]  # [1250, -200, 1]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_square_root_market_slippage__with_volume(self):
        """The volatility used by the slippage model is mocked to be equal to 0.1. The volume is equal to 50.0"""
        price_impact = 0.1
        max_volume_share_limit = 0.1
        close_prices_volatility = 0.1
        prices_without_slippage = [20.0, 30.0, 40.0]

        slippage_model = SquareRootMarketImpactSlippage(price_impact=price_impact,
                                                        data_provider=self.data_provider,
                                                        max_volume_share_limit=max_volume_share_limit)
        slippage_model._compute_volatility = Mock()
        slippage_model._compute_volatility.return_value = close_prices_volatility

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date('2020-01-01'),
                                                                                self.orders,
                                                                                prices_without_slippage)

        expected_fill_prices = [20.0 + 20.0 * price_impact * close_prices_volatility * math.sqrt(5.0 / 50.0),
                                30.0 - 30.0 * price_impact * close_prices_volatility * math.sqrt(5.0 / 50.0),
                                40.0 + 40.0 * price_impact * close_prices_volatility * math.sqrt(1 / 50.0)]

        expected_fill_volumes = [5.0, -5.0, 1.0]

        assert_lists_equal(expected_fill_prices, actual_fill_prices)
        assert_lists_equal(expected_fill_volumes, actual_fill_volumes)

    def test_square_root_market_slippage__nan_volatility(self):
        price_impact = 0.1
        close_prices_volatility = float('nan')

        prices_without_slippage = [float('nan'), np.nan, 40]
        expected_fill_prices = [float('nan'), float('nan'), float('nan')]

        slippage_model = SquareRootMarketImpactSlippage(price_impact=price_impact,
                                                        data_provider=self.data_provider)

        slippage_model._compute_volatility = Mock()
        slippage_model._compute_volatility.return_value = close_prices_volatility

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)
        assert_lists_equal(expected_fill_prices, actual_fill_prices)

    def test_square_root_market_slippage__nan_prices_without_slippage(self):
        price_impact = 0.1
        slippage_model = SquareRootMarketImpactSlippage(price_impact=price_impact,
                                                        data_provider=self.data_provider)

        prices_without_slippage = [float('nan'), np.nan, float('nan')]
        expected_fill_prices = [float('nan'), float('nan'), float('nan')]

        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)
        assert_lists_equal(expected_fill_prices, actual_fill_prices)

    def test_square_root_market_slippage__nan_average_daily_volume(self):
        price_impact = 0.1
        avg_daily_volume = float('nan')

        prices_without_slippage = [20, 30, 40]
        expected_fill_prices = [float('nan'), float('nan'), float('nan')]

        slippage_model = SquareRootMarketImpactSlippage(price_impact=price_impact,
                                                        data_provider=self.data_provider)
        slippage_model._compute_average_volume = Mock()
        slippage_model._compute_average_volume.return_value = avg_daily_volume
        actual_fill_prices, actual_fill_volumes = slippage_model.process_orders(str_to_date("2020-01-01"),
                                                                                self.orders,
                                                                                prices_without_slippage)
        assert_lists_equal(expected_fill_prices, actual_fill_prices)


if __name__ == '__main__':
    unittest.main()
