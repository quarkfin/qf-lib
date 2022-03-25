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
from datetime import datetime

import pandas as pd
import numpy as np

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dimension_names import TICKERS, FIELDS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class TestPresetDataProvider(unittest.TestCase):
    ticker = BloombergTicker("Example US Equity")
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2019, 1, 1)

    @classmethod
    def setUpClass(cls) -> None:
        cls.data_provider_min_1 = PresetDataProvider(cls.mock_data_provider(Frequency.MIN_1), cls.start_date,
                                                     cls.end_date, Frequency.MIN_1)
        cls.data_provider_min_5 = PresetDataProvider(cls.mock_data_provider(Frequency.MIN_5), cls.start_date,
                                                     cls.end_date, Frequency.MIN_5)

    @classmethod
    def mock_data_provider(cls, frequency: Frequency) -> QFDataArray:
        cached_dates_idx = [y for x in pd.date_range(cls.start_date.date(), cls.end_date.date(), freq="B") for y in
                            pd.date_range(x + RelativeDelta(hour=13, minute=30), x + RelativeDelta(hour=20),
                                          freq=frequency.to_pandas_freq())]
        cached_tickers_idx = pd.Index([cls.ticker], name=TICKERS)
        cached_fields_idx = pd.Index(PriceField.ohlcv(), name=FIELDS)

        rng = np.random.default_rng(2021)
        data_array = QFDataArray.create(
            data=rng.integers(20, 50, (len(cached_dates_idx), len(cached_tickers_idx), len(cached_fields_idx))),
            dates=cached_dates_idx,
            tickers=[cls.ticker],
            fields=PriceField.ohlcv()
        )
        return data_array

    def test_get_price__1_minute_data_aggregation(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 2),
                                                  datetime(2017, 1, 2, 15), Frequency.MIN_1)
        data_5_min = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 2),
                                                        datetime(2017, 1, 2, 15), Frequency.MIN_5)
        data_15_min = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 2),
                                                         datetime(2017, 1, 2, 15), Frequency.MIN_15)
        data_60_min = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 2),
                                                         datetime(2017, 1, 2, 15), Frequency.MIN_60)

        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open],
                         data_5_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 34), PriceField.Close],
                         data_5_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30):datetime(2017, 1, 2, 13, 34), PriceField.Volume].sum(),
                         data_5_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Volume])

        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open],
                         data_15_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 44), PriceField.Close],
                         data_15_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30):datetime(2017, 1, 2, 13, 44), PriceField.Volume].sum(),
                         data_15_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Volume])

        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open],
                         data_60_min.loc[datetime(2017, 1, 2, 13), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 59), PriceField.Close],
                         data_60_min.loc[datetime(2017, 1, 2, 13), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30):datetime(2017, 1, 2, 13, 59), PriceField.Volume].sum(),
                         data_60_min.loc[datetime(2017, 1, 2, 13), PriceField.Volume])

    def test_get_price__5_minute_data_aggregation(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(),
                                                  datetime(2017, 1, 2), datetime(2017, 1, 2, 15), Frequency.MIN_5)
        data_15_min = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(),
                                                         datetime(2017, 1, 2), datetime(2017, 1, 2, 15),
                                                         Frequency.MIN_15)
        data_60_min = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(),
                                                         datetime(2017, 1, 2), datetime(2017, 1, 2, 15),
                                                         Frequency.MIN_60)

        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open],
                         data_15_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 40), PriceField.Close],
                         data_15_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30):datetime(2017, 1, 2, 13, 40), PriceField.Volume].sum(),
                         data_15_min.loc[datetime(2017, 1, 2, 13, 30), PriceField.Volume])

        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30), PriceField.Open],
                         data_60_min.loc[datetime(2017, 1, 2, 13), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 55), PriceField.Close],
                         data_60_min.loc[datetime(2017, 1, 2, 13), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 13, 30):datetime(2017, 1, 2, 13, 55), PriceField.Volume].sum(),
                         data_60_min.loc[datetime(2017, 1, 2, 13), PriceField.Volume])
