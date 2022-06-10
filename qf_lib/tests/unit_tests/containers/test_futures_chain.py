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

from numpy import nan
from pandas import date_range

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal


class TestFuturesChain(unittest.TestCase):

    def setUp(self) -> None:
        self.future_ticker = BloombergFutureTicker("Example", "EX{} Example", 1, 1, 10)
        tickers = [BloombergTicker("EXZ1 Example", SecurityType.FUTURE, 10),
                   BloombergTicker("EXH2 Example", SecurityType.FUTURE, 10)]
        self.exp_dates = {
            self.future_ticker: QFDataFrame(index=tickers, columns=[ExpirationDateField.LastTradeableDate],
                                            data=[str_to_date("2021-12-20"), str_to_date("2022-03-20")])
        }
        self.start_date = str_to_date("2021-12-17")
        self.end_date = str_to_date("2021-12-22")
        self.expiration_date = str_to_date("2021-12-20")
        self.data_array = QFDataArray.create(date_range(self.start_date, self.end_date), tickers,
                                             PriceField.ohlcv(),
                                             data=[
                                                 # 2021-12-17
                                                 [
                                                     # Open High  Low   Close Volume
                                                     [25.0, 25.1, 24.2, 26.0, 25.3],  # EXZ1 Example
                                                     [125.0, 125.1, 124.2, 126.0, 125.3],  # EXH2 Example
                                                 ],
                                                 # 2021-12-18
                                                 [
                                                     # Open High  Low   Close Volume
                                                     [26.0, 26.1, 26.2, 27.0, 26.3],
                                                     [127, 126.1, 126.2, 127.0, 126.3],
                                                 ],
                                                 # 2021-12-19
                                                 [
                                                     # Open High  Low   Close Volume
                                                     [29.8, 30.1, 29.2, 30.0, 30.3],
                                                     [130, 130.1, 129.2, 130.0, 130.3],
                                                 ],
                                                 # 2021-12-20
                                                 [
                                                     # Open High  Low   Close Volume
                                                     [34.0, 34.1, 33.2, 34.0, 34.3],
                                                     [133, 134.1, 133.2, 134.0, 134.3],
                                                 ],
                                                 # 2021-12-21
                                                 [
                                                     # Open High  Low   Close Volume
                                                     [38.0, 38.1, 36.2, 38.0, 38.3],
                                                     [137, 138.1, 136.2, 138.0, 138.3],
                                                 ],
                                                 # 2021-12-22
                                                 [
                                                     # Open High  Low   Close Volume
                                                     [40.0, 40.1, 35.2, 40.0, 40.3],
                                                     [141.1, 145.1, 135.2, 140.0, 140.3],
                                                 ],
                                             ])

    def test_future_chains(self):
        """ Open prices are available on the expiration date and the Close prices are available on the day before
        the expiration day. """
        data_provider = self._mock_data_provider(self.data_array)
        self._assert_adjustment_is_consistent(data_provider)

        difference_between_prices = 133.0 - 30.0  # Open price on the 20th and Close price on the 19th of December
        self._assert_adjustment_difference_is_correct(data_provider, difference_between_prices)

    def test_future_chains_if_no_open_price(self):
        """ Open price on the expiration day is set to nan. In that case the close price from that day should be taken
        to adjust the prices. """
        self.data_array.loc[self.expiration_date, :, PriceField.Open] = nan
        data_provider = self._mock_data_provider(self.data_array)
        self._assert_adjustment_is_consistent(data_provider)

        difference_between_prices = 134.0 - 30.0  # Close prices, 20th and 19th of December
        self._assert_adjustment_difference_is_correct(data_provider, difference_between_prices)

    def test_future_chains_if_no_close_price(self):
        """ Close price on the day before expiration day is set to nan. In that case the open price from that day should
        be taken to adjust the prices. """
        self.data_array.loc[str_to_date("2021-12-19"), :, PriceField.Close] = nan
        data_provider = self._mock_data_provider(self.data_array)
        self._assert_adjustment_is_consistent(data_provider)

        difference_between_prices = 133.0 - 29.8  # Open prices, 20th and 19th of December
        self._assert_adjustment_difference_is_correct(data_provider, difference_between_prices)

    def test_future_chains_if_no_close_nor_open_prices(self):
        """ Close price on the day before expiration day and the open price on the expiration day are set to nan. """
        self.data_array.loc[str_to_date("2021-12-19"), :, PriceField.Close] = nan
        self.data_array.loc[str_to_date("2021-12-20"), :, PriceField.Open] = nan

        data_provider = self._mock_data_provider(self.data_array)
        self._assert_adjustment_is_consistent(data_provider)

        difference_between_prices = 134.0 - 29.8  # Close price on the 20th, Open price on the 19th
        self._assert_adjustment_difference_is_correct(data_provider, difference_between_prices)

    def test_future_chains_if_no_open_prices(self):
        """ The newer contract does not have any open prices and its close price on the expiration date is also set to
        nan. In that case the futures chain on the expiration date will still not be adjusted! """
        self.data_array.loc[:, BloombergTicker("EXH2 Example"), PriceField.Open] = nan
        self.data_array.loc[str_to_date("2021-12-20"), :, PriceField.Close] = nan

        data_provider = self._mock_data_provider(self.data_array)

        difference_between_prices = 138.0 - 30.0  # Close price on the 21st, close price on the 19th
        self._assert_adjustment_difference_is_correct(data_provider, difference_between_prices)

    def _assert_adjustment_is_consistent(self, data_provider: DataProvider):
        """ Computes the adjusted futures chains on the expiration date and at the end date and compares if the
        adjustment is computed in the same way. """
        timer = SettableTimer()

        timer.set_current_time(self.expiration_date)
        self.future_ticker.initialize_data_provider(timer, data_provider)
        futures_chain_1 = FuturesChain(self.future_ticker, data_provider, FuturesAdjustmentMethod.BACK_ADJUSTED)
        prices = futures_chain_1.get_price(PriceField.ohlcv(), self.start_date, timer.now())

        timer.set_current_time(self.end_date)
        futures_chain_2 = FuturesChain(self.future_ticker, data_provider, FuturesAdjustmentMethod.BACK_ADJUSTED)
        prices_2 = futures_chain_2.get_price(PriceField.ohlcv(), self.start_date, timer.now())

        assert_dataframes_equal(prices.loc[:self.expiration_date], prices_2.loc[:self.expiration_date],
                                check_names=False)

    def _assert_adjustment_difference_is_correct(self, data_provider: DataProvider, expected_difference: float):
        """ Computes the adjusted and non adjusted futures chain and checks if all price values (OHLC) are adjusted
        by the correct value. """
        timer = SettableTimer(self.end_date)
        self.future_ticker.initialize_data_provider(timer, data_provider)

        adjusted_chain = FuturesChain(self.future_ticker, data_provider, FuturesAdjustmentMethod.BACK_ADJUSTED)
        adjusted_prices = adjusted_chain.get_price(PriceField.ohlcv(), self.start_date, timer.now())

        non_adjusted_chain = FuturesChain(self.future_ticker, data_provider, FuturesAdjustmentMethod.NTH_NEAREST)
        non_adjusted_prices = non_adjusted_chain.get_price(PriceField.ohlcv(), self.start_date, timer.now())

        fields_to_adjust = [PriceField.Open, PriceField.Close, PriceField.High, PriceField.Low]
        fields_without_adjustment = [PriceField.Volume]

        # Prices before the expiration date should be adjusted
        day_before_exp_date = self.expiration_date - RelativeDelta(days=1)
        assert_dataframes_equal(adjusted_prices.loc[:day_before_exp_date, fields_to_adjust],
                                non_adjusted_prices.loc[:day_before_exp_date, fields_to_adjust] + expected_difference,
                                check_names=False)
        assert_dataframes_equal(adjusted_prices.loc[:day_before_exp_date, fields_without_adjustment],
                                non_adjusted_prices.loc[:day_before_exp_date, fields_without_adjustment],
                                check_names=False)

        # Prices after the expiration date should not be adjusted
        assert_dataframes_equal(adjusted_prices.loc[self.expiration_date:],
                                non_adjusted_prices.loc[self.expiration_date:], check_names=False)

    def _mock_data_provider(self, data_array: QFDataArray):
        return PresetDataProvider(data_array, self.start_date, self.end_date, Frequency.DAILY, self.exp_dates)
