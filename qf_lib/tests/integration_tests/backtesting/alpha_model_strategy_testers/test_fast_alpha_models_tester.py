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
from itertools import cycle, islice
from unittest import TestCase

import numpy as np
import pandas as pd
from pandas.tseries.offsets import Day

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.fast_alpha_model_tester.fast_alpha_models_tester import FastAlphaModelTester, \
    FastAlphaModelTesterConfig
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker, Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestFastAlphaModelsTester(TestCase):
    apple_ticker = QuandlTicker("AAPL", "WIKI")
    ibm_ticker = QuandlTicker("IBM", "WIKI")
    tickers = [apple_ticker, ibm_ticker]

    test_start_date = str_to_date("2015-01-01")
    test_end_date = str_to_date("2015-01-31")

    data_start_date = str_to_date("2014-12-25")
    data_end_date = test_end_date

    frequency = Frequency.DAILY

    MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
    MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    def setUp(self):
        all_fields = PriceField.ohlcv()

        self._mocked_prices_arr = self._make_mock_data_array(self.tickers, all_fields)
        price_provider_mock = PresetDataProvider(self._mocked_prices_arr, self.data_start_date,
                                                 self.data_end_date, self.frequency)
        self.timer = SettableTimer()
        self.data_handler = DailyDataHandler(price_provider_mock, self.timer)
        self.alpha_model_type = DummyAlphaModel

    @classmethod
    def _make_mock_data_array(cls, tickers, fields):
        all_dates_index = pd.bdate_range(start=cls.data_start_date, end=cls.test_end_date)

        num_of_dates = len(all_dates_index)
        num_of_tickers = len(tickers)
        num_of_fields = len(fields)

        start_value = 100.0
        values = np.arange(start_value, num_of_dates * num_of_tickers * num_of_fields + start_value)
        reshaped_values = np.reshape(values, (num_of_dates, num_of_tickers, num_of_fields))

        mocked_result = QFDataArray.create(all_dates_index, tickers, fields, data=reshaped_values)
        mocked_result.loc[:, :, PriceField.Low] -= 50.0
        mocked_result.loc[:, :, PriceField.High] += 50.0

        return mocked_result

    def test_alpha_models_tester(self):
        first_param_set = (10, Exposure.LONG)
        second_param_set = (5, Exposure.SHORT)
        data_handler = self.data_handler

        params = [FastAlphaModelTesterConfig(self.alpha_model_type,
                                             {"period_length": 10, "first_suggested_exposure": Exposure.LONG,
                                              "risk_estimation_factor": None},
                                             ("period_length", "first_suggested_exposure")),
                  FastAlphaModelTesterConfig(self.alpha_model_type,
                                             {"period_length": 5, "first_suggested_exposure": Exposure.SHORT,
                                              "risk_estimation_factor": None},
                                             ("period_length", "first_suggested_exposure"))]

        tester = FastAlphaModelTester(params, self.tickers, self.test_start_date, self.test_end_date, data_handler,
                                      self.timer)

        backtest_summary = tester.test_alpha_models()
        self.assertEqual(self.tickers, backtest_summary.tickers)
        self.assertEqual(DummyAlphaModel, backtest_summary.alpha_model_type)

        backtest_summary_elements = backtest_summary.elements_list
        self.assertEqual(2 * (len(self.tickers) + 1), len(backtest_summary_elements))

        # check first backtest summary element - trades
        first_elem = backtest_summary_elements[2]
        self.assertEqual(first_param_set, first_elem.model_parameters)

        expected_trades_data = [
            [self.apple_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-16"), (260.0 / 160.0 - 1), 1.0],
            [self.ibm_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-16"), (265.0 / 165.0 - 1), 1.0]
        ]

        generated_trades_data = [
            [t.ticker, t.start_time, t.end_time, t.pnl, t.direction] for t in first_elem.trades
        ]

        self.assertCountEqual(generated_trades_data, expected_trades_data)

        # check first backtest summary element - returns
        all_dates_index = pd.date_range(start=self.test_start_date + Day(2), end=self.test_end_date)
        expected_returns = SimpleReturnsSeries(index=all_dates_index, data=[
            0.0000000, 0.0000000,
            0.0615530, 0.0579832, 0.0548048, 0.0519568, 0.0493902,
            0.0000000, 0.0000000,
            0.0470653, 0.0449495, 0.0430157, 0.0412415, 0.0396078,
            0.0000000, 0.0000000,
            0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000,
            0.0000000, 0.0000000,
            0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000,
            0.0000000
        ])
        assert_series_equal(expected_returns, first_elem.returns_tms)

        # check second backtest summary element
        second_elem = backtest_summary_elements[5]
        self.assertEqual(second_param_set, second_elem.model_parameters)

        expected_trades_data = [
            [self.apple_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-09"), (1 - 210.0 / 160.0), -1.0],
            [self.apple_ticker, str_to_date("2015-01-16"), str_to_date("2015-01-23"), (310.0 / 260.0 - 1), 1.0],
            [self.apple_ticker, str_to_date("2015-01-23"), str_to_date("2015-01-30"), (1 - 360.0 / 310.0), -1.0],
            [self.ibm_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-09"), (1 - 215.0 / 165.0), -1.0],
            [self.ibm_ticker, str_to_date("2015-01-16"), str_to_date("2015-01-23"), (315.0 / 265.0 - 1), 1.0],
            [self.ibm_ticker, str_to_date("2015-01-23"), str_to_date("2015-01-30"), (1 - 365.0 / 315.0), -1.0]
        ]
        generated_trades_data = [
            [t.ticker, t.start_time, t.end_time, t.pnl, t.direction]
            for t in second_elem.trades
        ]
        self.assertCountEqual(expected_trades_data, generated_trades_data)

        # check second backtest summary element - returns
        all_dates_index = pd.date_range(start=self.test_start_date + Day(2), end=self.test_end_date)
        expected_returns = SimpleReturnsSeries(index=all_dates_index, data=[
            0.0000000, 0.0000000,
            -0.0615530, - 0.0579832, - 0.0548048, - 0.0519568, - 0.0493902,
            0.0000000, 0.0000000,
            0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000,
            0.0000000, 0.0000000,
            0.0380987, 0.0367003, 0.0354010, 0.0341905, 0.0330601,
            0.0000000, 0.0000000,
            - 0.0320020, - 0.0310096, - 0.0300769, - 0.0291986, - 0.0283702,
            0.0000000
        ])
        assert_series_equal(expected_returns, second_elem.returns_tms)


class DummyAlphaModel(AlphaModel):
    def __init__(self, period_length: int, first_suggested_exposure: Exposure,
                 risk_estimation_factor: float, data_provider: DataHandler = None):
        super().__init__(risk_estimation_factor, data_provider)

        assert first_suggested_exposure != Exposure.OUT

        self.timer = data_provider.timer

        last_suggested_exposure = Exposure.LONG if first_suggested_exposure == Exposure.SHORT else Exposure.SHORT

        dates = pd.bdate_range(TestFastAlphaModelsTester.test_start_date, TestFastAlphaModelsTester.test_end_date)
        dates_index = pd.DatetimeIndex(dates)

        signals_cycle = cycle(
            [first_suggested_exposure] * period_length +
            [Exposure.OUT] * period_length +
            [last_suggested_exposure] * period_length
        )

        num_of_dates = len(dates_index)
        exposures_list = list(islice(signals_cycle, 0, num_of_dates))
        self._exposures = QFSeries(index=dates_index, data=exposures_list)

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime,
                           frequency: Frequency) -> Exposure:
        try:
            exposure = self._exposures[current_time]
        except KeyError:
            exposure = current_exposure
        return exposure


if __name__ == '__main__':
    unittest.main()
