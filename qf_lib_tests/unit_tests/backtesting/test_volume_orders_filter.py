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
import unittest
from typing import Optional

import pandas as pd

from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.orders_filter.volume_orders_filter import VolumeOrdersFilter
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.helpers import tickers_dict_to_data_array
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class TestVolumeOrdersFilter(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        """ Setup a preset data provider and a scenario, in which the sized orders will exceed the volume limits. """
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})
        cls.ticker = BloombergTicker("Example Index")

    def test_volume_orders_filter__resize_orders(self):
        """Tests VolumeOrdersVerifier with orders exceeding the limit."""
        # Setup DataHandler and VolumeOrdersVerifier
        volume_percentage_limit = 0.15
        volume_value = 100.0
        data_handler = self._setup_data_handler(volume_value)
        volume_orders_verifier = VolumeOrdersFilter(data_handler, volume_percentage_limit)

        # Initialize a list of orders, which exceed the maximum volume limit
        buy_orders = [Order(self.ticker, 100, MarketOrder(), TimeInForce.GTC)]
        sell_orders = [Order(self.ticker, 100, MarketOrder(), TimeInForce.GTC)]

        new_buy_orders = volume_orders_verifier.adjust_orders(buy_orders)
        new_sell_orders = volume_orders_verifier.adjust_orders(sell_orders)

        self.assertEqual(len(new_buy_orders), len(buy_orders))
        self.assertEqual(len(new_sell_orders), len(sell_orders))

        for order in new_buy_orders + new_sell_orders:
            self.assertLessEqual(abs(order.quantity), abs(volume_value * volume_percentage_limit))

    def test_volume_orders_filter__no_resize_orders(self):
        """Tests if VolumeOrdersVerifier does not change orders, which do not exceed the limit."""
        # Setup DataHandler and VolumeOrdersVerifier
        volume_percentage_limit = 0.15
        volume_value = 100.0
        data_handler = self._setup_data_handler(volume_value)
        volume_orders_verifier = VolumeOrdersFilter(data_handler, volume_percentage_limit)

        # Initialize a list of orders, which do not exceed the maximum volume limit
        max_quantity = int(volume_percentage_limit * volume_value)
        orders = [Order(self.ticker, max_quantity, MarketOrder(), TimeInForce.GTC),
                  Order(self.ticker, -max_quantity // 2, MarketOrder(), TimeInForce.GTC),
                  Order(self.ticker, max_quantity // 3, MarketOrder(), TimeInForce.GTC)]

        new_orders = volume_orders_verifier.adjust_orders(orders)
        self.assertCountEqual(orders, new_orders)

    def test_volume_orders_filter__no_volume_data(self):
        """Tests if VolumeOrdersVerifier does not change orders, which do not have the volume data."""
        # Setup DataHandler and VolumeOrdersVerifier
        volume_percentage_limit = 0.15
        volume_value = None
        data_handler = self._setup_data_handler(volume_value)
        volume_orders_verifier = VolumeOrdersFilter(data_handler, volume_percentage_limit)

        # Initialize a list of orders, which do not exceed the maximum volume limit
        orders = [Order(self.ticker, 100, MarketOrder(), TimeInForce.GTC),
                  Order(self.ticker, 200, MarketOrder(), TimeInForce.GTC),
                  Order(self.ticker, -300, MarketOrder(), TimeInForce.GTC)]

        new_orders = volume_orders_verifier.adjust_orders(orders)
        self.assertCountEqual(orders, new_orders)

    def test_volume_orders_filter__adjust_buy_stop_orders(self):
        """
        Test if StopOrders are adjusted in a correct way. Suppose, the StopOrder quantity will be much bigger than
        the current MarketOrder, because the position for the ticker already existed for some time, e.g.
        - there exists an open LONG position of size 100
        - the position needs to be adjusted to 200
        - a new MarketOrder of size 100 is created
        - a new StopOrder of size -200 is created
        - the volume percentage limit limits the MarketOrder to 15% of avg daily volume (set to volume_value = 100)
        - then the StopOrder needs to be adjusted to -115
        """

        volume_percentage_limit = 0.15
        volume_value = 100.0
        data_handler = self._setup_data_handler(volume_value)
        volume_orders_verifier = VolumeOrdersFilter(data_handler, volume_percentage_limit)

        # Initialize a list of orders, which do not exceed the maximum volume limit
        buy_order = [Order(self.ticker, 100, MarketOrder(), TimeInForce.GTC),
                     Order(self.ticker, -200, StopOrder(1.0), TimeInForce.GTC)]

        new_orders = volume_orders_verifier.adjust_orders(buy_order)

        expected_buy_order = [Order(self.ticker, 15, MarketOrder(), TimeInForce.GTC),
                              Order(self.ticker, -115, StopOrder(1.0), TimeInForce.GTC)]
        self.assertCountEqual(new_orders, expected_buy_order)

    def test_volume_orders_filter__adjust_sell_stop_orders(self):
        """
        Test if StopOrders are adjusted in a correct way. The MarketOrder corresponding to StopOrder is a sell order.
        """

        volume_percentage_limit = 0.15
        volume_value = 100.0
        data_handler = self._setup_data_handler(volume_value)
        volume_orders_verifier = VolumeOrdersFilter(data_handler, volume_percentage_limit)

        # Initialize a list of orders, which do not exceed the maximum volume limit
        sell_order = [Order(self.ticker, -100, MarketOrder(), TimeInForce.GTC),
                      Order(self.ticker, 200, StopOrder(1.0), TimeInForce.GTC)]

        new_orders = volume_orders_verifier.adjust_orders(sell_order)

        expected_sell_order = [Order(self.ticker, -15, MarketOrder(), TimeInForce.GTC),
                               Order(self.ticker, 115, StopOrder(1.0), TimeInForce.GTC)]
        self.assertCountEqual(new_orders, expected_sell_order)

    def _setup_data_handler(self, volume_value: Optional[float]) -> DataHandler:
        dates = pd.date_range(str_to_date("2019-12-01"), str_to_date("2020-01-30"), freq='D')
        prices_data_frame = QFDataFrame(data={PriceField.Volume: [volume_value] * len(dates)},
                                        index=dates)

        prices_data_array = tickers_dict_to_data_array({
            self.ticker: prices_data_frame,
        }, [self.ticker], [PriceField.Volume])

        data_provider = PresetDataProvider(prices_data_array, dates[0], dates[-1], Frequency.DAILY)
        timer = SettableTimer(dates[-1])

        return DailyDataHandler(data_provider, timer)
