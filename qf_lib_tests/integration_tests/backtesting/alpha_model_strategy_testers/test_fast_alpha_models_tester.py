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
from itertools import cycle, islice
from unittest import TestCase

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
from pandas.util.testing import assert_frame_equal, assert_series_equal

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.fast_alpha_model_tester.fast_alpha_models_tester import FastAlphaModelTester
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.tickers.tickers import QuandlTicker, Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer, Timer
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class TestFastAlphaModelsTester(TestCase):
    apple_ticker = QuandlTicker("AAPL", "WIKI")
    ibm_ticker = QuandlTicker("IBM", "WIKI")
    tickers = [apple_ticker, ibm_ticker]

    test_start_date = str_to_date("2015-01-01")
    test_end_date = str_to_date("2015-01-31")

    data_start_date = str_to_date("2014-12-25")
    data_end_date = test_end_date

    frequency = Frequency.DAILY

    def setUp(self):
        all_fields = PriceField.ohlcv()

        self._mocked_prices_arr = self._make_mock_data_array(self.tickers, all_fields)
        self._price_provider_mock = PresetDataProvider(self._mocked_prices_arr,
                                                       self.data_start_date, self.data_end_date, self.frequency)
        self.timer = SettableTimer()
        self._alpha_model_factory = DummyAlphaModelFactory(self.timer)  # type: AlphaModelFactory

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
        parameter_lists = (first_param_set, second_param_set)

        tester = FastAlphaModelTester(self.alpha_model_type, parameter_lists, self.tickers,
                                      self.test_start_date, self.test_end_date, self._price_provider_mock,
                                      self.timer, self._alpha_model_factory)

        backtest_summary = tester.test_alpha_models()
        self.assertEqual(self.tickers, backtest_summary.tickers)
        self.assertEqual(DummyAlphaModel, backtest_summary.alpha_model_type)

        backtest_summary_elements = backtest_summary.elements_list
        self.assertEqual(2, len(backtest_summary_elements))

        # check first backtest summary element - trades
        first_elem = backtest_summary_elements[0]
        self.assertEqual(first_param_set, first_elem.model_parameters)

        trade_columns = pd.Index([TradeField.Ticker, TradeField.StartDate, TradeField.EndDate, TradeField.Open,
                                  TradeField.MaxGain, TradeField.MaxLoss, TradeField.Close, TradeField.Return,
                                  TradeField.Exposure])

        expected_trades = pd.DataFrame(columns=trade_columns, data=[
            [
                self.apple_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-16"),
                160.0, 141.0, -48.0, 260.0, 260.0 / 160.0 - 1, 1.0
            ],
            [
                self.ibm_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-16"),
                165.0, 141.0, -48.0, 265.0, 265.0 / 165.0 - 1, 1.0
            ]
        ])
        assert_frame_equal(expected_trades, first_elem.trades_df)

        # check first backtest summary element - returns
        all_dates_index = pd.bdate_range(start=self.test_start_date + BDay(2), end=self.test_end_date, name='dates')
        expected_returns = SimpleReturnsSeries(index=all_dates_index, data=[
            0.0615530, 0.0579832, 0.0548048, 0.0519568, 0.0493902,
            0.0470653, 0.0449495, 0.0430157, 0.0412415, 0.0396078,
            0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000,
            0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000
        ])
        assert_series_equal(expected_returns, first_elem.returns_tms)

        # check second backtest summary element
        second_elem = backtest_summary_elements[1]
        self.assertEqual(second_param_set, second_elem.model_parameters)

        trade_columns = pd.Index([TradeField.Ticker, TradeField.StartDate, TradeField.EndDate, TradeField.Open,
                                  TradeField.MaxGain, TradeField.MaxLoss, TradeField.Close, TradeField.Return,
                                  TradeField.Exposure])

        expected_trades = pd.DataFrame(columns=trade_columns, data=[
            [
                self.apple_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-09"),
                160.0, 48.0, -91.0, 210.0, 1 - 210.0 / 160.0, -1.0
            ],
            [
                self.apple_ticker, str_to_date("2015-01-16"), str_to_date("2015-01-23"),
                260.0, 91.0, -48.0, 310.0, 310.0 / 260.0 - 1, 1.0
            ],
            [
                self.apple_ticker, str_to_date("2015-01-23"), str_to_date("2015-01-30"),
                310.0, 48.0, -91.0, 360.0, 1 - 360.0 / 310.0, -1.0
            ],
            [
                self.ibm_ticker, str_to_date("2015-01-02"), str_to_date("2015-01-09"),
                165.0, 48.0, -91.0, 215.0, 1 - 215.0 / 165.0, -1.0
            ],
            [
                self.ibm_ticker, str_to_date("2015-01-16"), str_to_date("2015-01-23"),
                265.0, 91.0, -48.0, 315.0, 315.0 / 265.0 - 1, 1.0
            ],
            [
                self.ibm_ticker, str_to_date("2015-01-23"), str_to_date("2015-01-30"),
                315.0, 48.0, -91.0, 365.0, 1 - 365.0 / 315.0, -1.0
            ]
        ])
        assert_frame_equal(expected_trades, second_elem.trades_df)

        # check second backtest summary element - returns
        all_dates_index = pd.bdate_range(start=self.test_start_date + BDay(2), end=self.test_end_date, name='dates')
        expected_returns = SimpleReturnsSeries(index=all_dates_index, data=[
            -0.0615530, - 0.0579832, - 0.0548048, - 0.0519568, - 0.0493902,
            0.0000000, 0.0000000, 0.0000000, 0.0000000, 0.0000000,
            0.0380987, 0.0367003, 0.0354010, 0.0341905, 0.0330601,
            - 0.0320020, - 0.0310096, - 0.0300769, - 0.0291986, - 0.0283702
        ])
        assert_series_equal(expected_returns, second_elem.returns_tms)


class DummyAlphaModel(AlphaModel):
    def __init__(self, period_length: int, first_suggested_exposure: Exposure, timer: Timer):
        super().__init__(0.0, None)

        assert first_suggested_exposure != Exposure.OUT

        self.timer = timer

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
        self._exposures = pd.Series(index=dates_index, data=exposures_list)

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure) -> Exposure:
        exposure = self._exposures[self.timer.now()]
        return exposure


class DummyAlphaModelFactory(object):
    def __init__(self, timer: Timer):
        self.timer = timer

    def make_model(self, model_type, *params):
        assert model_type == DummyAlphaModel
        period_length, first_suggested_exposure = params
        return DummyAlphaModel(period_length, first_suggested_exposure, self.timer)


if __name__ == '__main__':
    unittest.main()
