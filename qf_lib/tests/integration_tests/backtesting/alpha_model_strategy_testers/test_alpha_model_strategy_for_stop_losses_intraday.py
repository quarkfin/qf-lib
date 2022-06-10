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
import numpy as np
import pandas as pd
from numpy.testing import assert_equal, assert_almost_equal

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.tests.integration_tests.backtesting.alpha_model_strategy_testers.test_alpha_model_strategy_for_stop_losses import \
    TestAlphaModelStrategy


class TestAlphaModelIntradayStrategy(TestAlphaModelStrategy):
    data_start_date = str_to_date("2014-12-25 00:00:00.00", DateFormat.FULL_ISO)
    data_end_date = str_to_date("2015-02-28 23:59:59.00", DateFormat.FULL_ISO)
    end_date = str_to_date("2015-02-28 13:30:00.00", DateFormat.FULL_ISO)

    frequency = Frequency.MIN_1

    def test_stop_losses(self):
        expected_transactions_quantities = \
            [8130, -127, 1, -8004, 7454, -58, -7396, 6900, -6900, 6390, -44, -6346, 5718, -36]

        result_transactions_quantities = [t.quantity for t in self.transactions]
        assert_equal(expected_transactions_quantities, result_transactions_quantities)

        expected_transactions_prices = [125, 130, 135, 235.6, 255, 260, 259.35, 280, 264.1, 285, 290, 282, 315, 320]
        result_transactions_prices = [t.price for t in self.transactions]
        assert_almost_equal(expected_transactions_prices, result_transactions_prices)

        expected_portfolio_values = [1024390, 1064659, 1064659, 1064659, 1104677, 1144697, 1184717, 1224737, 1264757,
                                     1264757, 1264757, 1304777, 1344797, 1384817, 1424837, 1464857, 1464857, 1464857,
                                     1504877, 1544897, 1584917, 1624937, 1664957, 1664957, 1664957, 1704977, 1744997,
                                     1785017, 1825037, 1865057, 1865057, 1865057, 1905077, 1945097, 1985117, 1885867.4,
                                     1908229.4, 1908229.4, 1908229.4, 1945325.4, 1982305.4, 2019285.4, 1918330, 1808620,
                                     1808620, 1808620, 1827790, 1859608, 1891338, 1923068, 1954798, 1954798, 1954798,
                                     1789802, 1806956, 1835438, 1863848, 1892258, 1892258]
        assert_almost_equal(expected_portfolio_values, list(self.portfolio.portfolio_eod_series()))

    def _make_mock_data_array(self, tickers, fields):
        all_dates_market_open = pd.date_range(start=self.data_start_date + MarketOpenEvent.trigger_time(),
                                              end=self.data_end_date + MarketOpenEvent.trigger_time(), freq="B")
        all_dates_market_close = pd.date_range(start=self.data_start_date + MarketCloseEvent.trigger_time() - Frequency.MIN_1.time_delta(),
                                               end=self.data_end_date + MarketCloseEvent.trigger_time() - Frequency.MIN_1.time_delta(), freq="B")

        num_of_dates = len(all_dates_market_open)
        num_of_tickers = len(tickers)
        num_of_fields = len(fields)

        start_value = 100.0
        values = np.arange(start_value, num_of_dates * num_of_tickers * num_of_fields + start_value)
        reshaped_values = np.reshape(values, (num_of_dates, num_of_tickers, num_of_fields))

        mocked_result_market_open = QFDataArray.create(all_dates_market_open, tickers, fields, data=reshaped_values)

        mocked_result_market_close = QFDataArray.create(all_dates_market_close, tickers, fields, data=reshaped_values)
        mocked_result_market_close.loc[:, :, PriceField.Low] -= 5.0
        mocked_result_market_close.loc[:, :, PriceField.High] += 5.0

        all_dates = all_dates_market_open.union(all_dates_market_close)

        mocked_result = QFDataArray.create(all_dates, tickers, fields)
        mocked_result.loc[all_dates_market_open, :, :] = mocked_result_market_open.loc[:, :, :]
        mocked_result.loc[all_dates_market_close, :, :] = mocked_result_market_close.loc[:, :, :]

        self._add_test_cases(mocked_result, tickers)
        return mocked_result

    def _add_test_cases(self, mocked_result, tickers):
        # single low price breaking the stop level
        mocked_result.loc[
            str_to_date('2015-02-05 19:59:00.00', DateFormat.FULL_ISO), tickers[0], PriceField.Low] -= 15.0
        # two consecutive low prices breaking the stop level
        mocked_result.loc[
            str_to_date('2015-02-12 19:59:00.00', DateFormat.FULL_ISO), tickers[0], PriceField.Low] -= 15.0
        mocked_result.loc[
            str_to_date('2015-02-13 19:59:00.00', DateFormat.FULL_ISO), tickers[0], PriceField.Low] -= 15.0
        # single open price breaking the stop level
        mocked_result.loc[
            str_to_date('2015-02-23 19:59:00.00', DateFormat.FULL_ISO), tickers[0], PriceField.Low] -= 25.0
        mocked_result.loc[str_to_date('2015-02-23 19:59:00.00', DateFormat.FULL_ISO), tickers[0], PriceField.Open] = \
            mocked_result.loc[str_to_date('2015-02-23 19:59:00.00', DateFormat.FULL_ISO), tickers[0], PriceField.Low]
