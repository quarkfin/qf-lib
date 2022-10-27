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
from datetime import datetime

import pandas as pd
import numpy as np
from pandas import DatetimeIndex

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dimension_names import TICKERS, FIELDS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class TestPresetDataProvider(unittest.TestCase):
    ticker = BloombergTicker("Example US Equity")
    tickers = [BloombergTicker("Example US Equity"), BloombergTicker("Example EU Equity")]
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2019, 1, 1)

    @classmethod
    def setUpClass(cls) -> None:
        cls.data_provider_daily = PresetDataProvider(cls.mock_data_provider(Frequency.DAILY), cls.start_date,
                                                     cls.end_date, Frequency.DAILY)
        cls.data_provider_min_1 = PresetDataProvider(cls.mock_data_provider(Frequency.MIN_1), cls.start_date,
                                                     cls.end_date, Frequency.MIN_1)
        cls.data_provider_min_5 = PresetDataProvider(cls.mock_data_provider(Frequency.MIN_5), cls.start_date,
                                                     cls.end_date, Frequency.MIN_5)

    @classmethod
    def mock_data_provider(cls, frequency: Frequency) -> QFDataArray:
        if frequency == Frequency.DAILY:
            r_delta_start = RelativeDelta(hour=0, minute=0)
            r_delta_end = RelativeDelta(hour=0)
        else:
            r_delta_start = RelativeDelta(hour=13, minute=30)
            r_delta_end = RelativeDelta(hour=20)

        cached_dates_idx = [y for x in pd.date_range(cls.start_date.date(), cls.end_date.date(), freq="B") for y in
                            pd.date_range(x + r_delta_start, x + r_delta_end, freq=frequency.to_pandas_freq())]

        cached_tickers_idx = pd.Index(cls.tickers, name=TICKERS)
        cached_fields_idx = pd.Index(PriceField.ohlcv(), name=FIELDS)

        rng = np.random.default_rng(2021)
        data_array = QFDataArray.create(
            data=rng.integers(20, 50, (len(cached_dates_idx), len(cached_tickers_idx), len(cached_fields_idx))),
            dates=cached_dates_idx,
            tickers=cls.tickers,
            fields=PriceField.ohlcv()
        )
        return data_array

    def test_get_last_available_price_invalid_end_date(self):
        data = self.data_provider_min_1.get_last_available_price(self.ticker, frequency=Frequency.MIN_1)

        self.assertTrue(math.isnan(data))

    def test_get_last_available_price_valid_end_date(self):
        data = self.data_provider_min_1.get_last_available_price(self.ticker, frequency=Frequency.MIN_1,
                                                                 end_time=datetime(2018, 6, 23, 15, 21))

        self.assertFalse(math.isnan(data))

    def test_get_last_available_price_invalid_end_date_multiple_tickers(self):
        data = self.data_provider_min_1.get_last_available_price(self.tickers, frequency=Frequency.MIN_1)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(self.tickers),))
        self.assertListEqual(list(data.index), self.tickers)

    def test_get_last_available_price_valid_end_date_multiple_tickers(self):
        data = self.data_provider_min_1.get_last_available_price(self.tickers, frequency=Frequency.MIN_1,
                                                                 end_time=datetime(2018, 6, 23, 15, 21))

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(self.tickers),))
        self.assertListEqual(list(data.index), self.tickers)

    def test_get_price_daily(self):
        data = self.data_provider_daily.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 3),
                                                  datetime(2017, 1, 3), Frequency.DAILY)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (5,))

        data = self.data_provider_daily.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 2),
                                                  datetime(2017, 1, 3), Frequency.DAILY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (2, 5))

    def test_get_price_on_weekend_empty_data_daily(self):
        data = self.data_provider_daily.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 21), datetime(2017, 1, 21),
                                                  Frequency.DAILY)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(PriceField.ohlcv()),))
        self.assertTrue(data.isnull().values.all())

    def test_get_price_single_ticker_single_field_single_date_daily(self):
        data = self.data_provider_daily.get_price(self.ticker, PriceField.Close, datetime(2017, 1, 3),
                                                  datetime(2017, 1, 3), Frequency.DAILY)

        self.assertEqual(type(data), int)

    def test_get_price_single_ticker_single_field_multiple_dates_daily(self):
        data = self.data_provider_daily.get_price(self.ticker, PriceField.Close, datetime(2017, 1, 3),
                                                  datetime(2017, 1, 5), Frequency.DAILY)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (3,))
        self.assertEqual(type(data.index), DatetimeIndex)
        self.assertEqual(data.index.shape, (3,))
        self.assertEqual(Frequency.infer_freq(data.index), Frequency.DAILY)
        self.assertEqual(data.name, self.ticker.as_string())

    def test_get_price_single_ticker_multiple_fields_single_single_date_daily(self):
        data = self.data_provider_daily.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 3),
                                                  datetime(2017, 1, 3), Frequency.DAILY)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(PriceField.ohlcv()),))
        self.assertListEqual(list(data.index), PriceField.ohlcv())
        self.assertEqual(data.index.shape, (len(PriceField.ohlcv()),))
        self.assertEqual(data.name, self.ticker.as_string())

    def test_get_price_multiple_tickers_single_field_single_date_daily(self):
        data = self.data_provider_daily.get_price(self.tickers, PriceField.Close, datetime(2017, 1, 3),
                                                  datetime(2017, 1, 3), Frequency.DAILY)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(self.tickers),))
        self.assertListEqual(list(data.index), self.tickers)
        self.assertEqual(data.index.shape, (len(self.tickers),))
        self.assertEqual(data.name, PriceField.Close)

    def test_get_price_single_ticker_multiple_fields_multiple_dates_daily(self):
        data = self.data_provider_daily.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 3),
                                                  datetime(2017, 1, 5), Frequency.DAILY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (3, len(PriceField.ohlcv())))
        self.assertEqual(type(data.index), DatetimeIndex)
        self.assertEqual(data.index.shape, (3,))
        self.assertEqual(Frequency.infer_freq(data.index), Frequency.DAILY)
        self.assertListEqual(list(data.columns), PriceField.ohlcv())

    def test_get_price_multiple_tickers_single_field_multiple_dates_daily(self):
        data = self.data_provider_daily.get_price(self.tickers, PriceField.Close, datetime(2017, 1, 3),
                                                  datetime(2017, 1, 5), Frequency.DAILY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (3, len(self.tickers)))
        self.assertEqual(type(data.index), DatetimeIndex)
        self.assertEqual(data.index.shape, (3,))
        self.assertEqual(Frequency.infer_freq(data.index), Frequency.DAILY)
        self.assertListEqual(list(data.columns), self.tickers)

    def test_get_price_multiple_tickers_multiple_fields_single_date_daily(self):
        data = self.data_provider_daily.get_price(self.tickers, PriceField.ohlcv(), datetime(2017, 1, 3),
                                                  datetime(2017, 1, 3), Frequency.DAILY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (len(self.tickers), len(PriceField.ohlcv())))
        self.assertListEqual(list(data.index), self.tickers)
        self.assertEqual(data.index.shape, (len(self.tickers),))
        self.assertListEqual(list(data.columns), PriceField.ohlcv())

    def test_get_price_multiple_tickers_multiple_fields_multiple_dates_daily(self):
        data = self.data_provider_daily.get_price(self.tickers, PriceField.ohlcv(), datetime(2017, 1, 3),
                                                  datetime(2017, 1, 5), Frequency.DAILY)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (3, len(self.tickers), len(PriceField.ohlcv())))
        self.assertEqual(len(data.dates), 3)
        self.assertListEqual(list(data.dates), list(pd.date_range(datetime(2017, 1, 3), datetime(2017, 1, 5),
                                                                  freq=Frequency.DAILY.to_pandas_freq())))
        self.assertEqual(Frequency.infer_freq(data.dates.values), Frequency.DAILY)
        self.assertEqual(len(data.fields), len(PriceField.ohlcv()))
        self.assertListEqual(list(data.fields), PriceField.ohlcv())
        self.assertEqual(len(data.tickers), len(self.tickers))
        self.assertListEqual(list(data.tickers), self.tickers)
        self.assertEqual(data.name, None)

    def test_get_price_on_weekend_empty_data__1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 21, 4), datetime(2017, 1, 21, 5),
                                                  Frequency.MIN_1)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (0, len(PriceField.ohlcv()),))
        self.assertTrue(data.isnull().values.all())

    def test_get_price_single_ticker_single_field_single_date_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.Close, datetime(2017, 1, 3, 13, 45),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), int)

    def test_get_price_single_ticker_single_field_multiple_dates_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.Close, datetime(2017, 1, 3, 13, 38),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (8,))
        self.assertEqual(type(data.index), DatetimeIndex)
        self.assertEqual(data.index.shape, (8,))
        self.assertEqual(Frequency.infer_freq(data.index), Frequency.MIN_1)
        self.assertEqual(data.name, self.ticker.as_string())

    def test_get_price_single_ticker_multiple_fields_single_single_date_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 3, 13, 45),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(PriceField.ohlcv()),))
        self.assertListEqual(list(data.index), PriceField.ohlcv())
        self.assertEqual(data.index.shape, (len(PriceField.ohlcv()),))
        self.assertEqual(data.name, self.ticker.as_string())

    def test_get_price_multiple_tickers_single_field_single_date_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.tickers, PriceField.Close, datetime(2017, 1, 3, 13, 45),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(data.shape, (len(self.tickers),))
        self.assertListEqual(list(data.index), self.tickers)
        self.assertEqual(data.index.shape, (len(self.tickers),))
        self.assertEqual(data.name, PriceField.Close)

    def test_get_price_single_ticker_multiple_fields_multiple_dates_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.ticker, PriceField.ohlcv(), datetime(2017, 1, 3, 13, 38),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (8, len(PriceField.ohlcv())))
        self.assertEqual(type(data.index), DatetimeIndex)
        self.assertEqual(data.index.shape, (8,))
        self.assertEqual(Frequency.infer_freq(data.index), Frequency.MIN_1)
        self.assertListEqual(list(data.columns), PriceField.ohlcv())

    def test_get_price_multiple_tickers_single_field_multiple_dates_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.tickers, PriceField.Close, datetime(2017, 1, 3, 13, 38),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (8, len(self.tickers)))
        self.assertEqual(type(data.index), DatetimeIndex)
        self.assertEqual(data.index.shape, (8,))
        self.assertEqual(Frequency.infer_freq(data.index), Frequency.MIN_1)
        self.assertListEqual(list(data.columns), self.tickers)

    def test_get_price_multiple_tickers_multiple_fields_single_date_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.tickers, PriceField.ohlcv(), datetime(2017, 1, 3, 13, 45),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (len(self.tickers), len(PriceField.ohlcv())))
        self.assertListEqual(list(data.index), self.tickers)
        self.assertEqual(data.index.shape, (len(self.tickers),))
        self.assertListEqual(list(data.columns), PriceField.ohlcv())

    def test_get_price_multiple_tickers_multiple_fields_multiple_dates_1_minute_data(self):
        data = self.data_provider_min_1.get_price(self.tickers, PriceField.ohlcv(), datetime(2017, 1, 3, 13, 38),
                                                  datetime(2017, 1, 3, 13, 45), Frequency.MIN_1)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (8, len(self.tickers), len(PriceField.ohlcv())))
        self.assertEqual(len(data.dates), 8)
        self.assertListEqual(list(data.dates), list(pd.date_range(datetime(2017, 1, 3, 13, 38), datetime(2017, 1, 3, 13, 45),
                                                                  freq=Frequency.MIN_1.to_pandas_freq())))
        self.assertEqual(Frequency.infer_freq(data.dates.values), Frequency.MIN_1)
        self.assertEqual(len(data.fields), len(PriceField.ohlcv()))
        self.assertListEqual(list(data.fields), PriceField.ohlcv())
        self.assertEqual(len(data.tickers), len(self.tickers))
        self.assertListEqual(list(data.tickers), self.tickers)
        self.assertEqual(data.name, None)

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

    def test_get_historical_price_minute_data_aggregation(self):
        no_of_bars = 3

        data = self.data_provider_min_1.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars * 60, datetime(2017, 1, 2, 15), Frequency.MIN_1)

        data_5_min = self.data_provider_min_1.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars, datetime(2017, 1, 2, 15), Frequency.MIN_5)
        data_15_min = self.data_provider_min_1.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars, datetime(2017, 1, 2, 15), Frequency.MIN_15)
        data_60_min = self.data_provider_min_1.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars, datetime(2017, 1, 2, 15), Frequency.MIN_60)

        self.assertEqual(data_5_min.shape[0], no_of_bars)
        self.assertEqual(data_15_min.shape[0], no_of_bars)
        self.assertEqual(data_60_min.shape[0], no_of_bars)

        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 55), PriceField.Open],
                         data_5_min.loc[datetime(2017, 1, 2, 14, 55), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 59), PriceField.Close],
                         data_5_min.loc[datetime(2017, 1, 2, 14, 55), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 55):datetime(2017, 1, 2, 14, 59), PriceField.Volume].sum(),
                         data_5_min.loc[datetime(2017, 1, 2, 14, 55), PriceField.Volume])

        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 45), PriceField.Open],
                         data_15_min.loc[datetime(2017, 1, 2, 14, 45), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 59), PriceField.Close],
                         data_15_min.loc[datetime(2017, 1, 2, 14, 45), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 45):datetime(2017, 1, 2, 14, 59), PriceField.Volume].sum(),
                         data_15_min.loc[datetime(2017, 1, 2, 14, 45), PriceField.Volume])

        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 0), PriceField.Open],
                         data_60_min.loc[datetime(2017, 1, 2, 14, 0), PriceField.Open])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 59), PriceField.Close],
                         data_60_min.loc[datetime(2017, 1, 2, 14, 0), PriceField.Close])
        self.assertEqual(data.loc[datetime(2017, 1, 2, 14, 0):datetime(2017, 1, 2, 14, 59), PriceField.Volume].sum(),
                         data_60_min.loc[datetime(2017, 1, 2, 14, 0), PriceField.Volume])

    def test_get_historical_price_days_data_aggregation(self):
        no_of_bars = 3

        data = self.data_provider_daily.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars * 31, datetime(2017, 1, 2), Frequency.DAILY)

        data_weekly = self.data_provider_daily.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars, datetime(2017, 1, 2), Frequency.WEEKLY)
        data_monthly = self.data_provider_daily.historical_price(
            self.ticker, PriceField.ohlcv(), no_of_bars, datetime(2017, 1, 2), Frequency.MONTHLY)

        self.assertEqual(data_weekly.shape[0], no_of_bars)
        self.assertEqual(data_monthly.shape[0], no_of_bars)

        self.assertEqual(data.loc[datetime(2016, 12, 26), PriceField.Open],
                         data_weekly.loc[datetime(2017, 1, 1), PriceField.Open])
        self.assertEqual(data.loc[datetime(2016, 12, 30), PriceField.Close],
                         data_weekly.loc[datetime(2017, 1, 1), PriceField.Close])
        self.assertEqual(data.loc[datetime(2016, 12, 26):datetime(2016, 12, 30), PriceField.Volume].sum(),
                         data_weekly.loc[datetime(2017, 1, 1), PriceField.Volume])

        self.assertEqual(data.loc[datetime(2016, 12, 1), PriceField.Open],
                         data_monthly.loc[datetime(2016, 12, 31), PriceField.Open])
        self.assertEqual(data.loc[datetime(2016, 12, 30), PriceField.Close],
                         data_monthly.loc[datetime(2016, 12, 31), PriceField.Close])
        self.assertEqual(data.loc[datetime(2016, 12, 1):datetime(2016, 12, 30), PriceField.Volume].sum(),
                         data_monthly.loc[datetime(2016, 12, 31), PriceField.Volume])
