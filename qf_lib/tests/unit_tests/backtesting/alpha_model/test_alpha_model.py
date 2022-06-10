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
from unittest.mock import patch, MagicMock, Mock

from pandas import date_range

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.average_true_range import average_true_range
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame


@patch.multiple(AlphaModel, __abstractmethods__=set())
class TestAlphaModel(unittest.TestCase):

    def setUp(self) -> None:
        self.ticker = BloombergTicker("Example Ticker")
        self.start_time = str_to_date('2020-01-01')
        self.end_time = str_to_date('2020-01-10')
        self.frequency = Frequency.DAILY

    def test_alpha_model__calculate_fraction_at_risk(self):
        data_handler = MagicMock()
        prices_df = PricesDataFrame.from_records(data=[(6.0, 4.0, 5.0) for _ in range(10)],
                                                 index=date_range(self.start_time, self.end_time),
                                                 columns=[PriceField.High, PriceField.Low, PriceField.Close])
        data_handler.historical_price.return_value = prices_df
        atr = average_true_range(prices_df, normalized=True)
        risk_estimation_factor = 3

        alpha_model = AlphaModel(risk_estimation_factor=risk_estimation_factor, data_provider=data_handler)
        fraction_at_risk = alpha_model.calculate_fraction_at_risk(self.ticker, self.end_time, self.frequency)
        self.assertEqual(risk_estimation_factor * atr, fraction_at_risk)

    @patch.object(AlphaModel, 'calculate_exposure')
    @patch.object(AlphaModel, 'calculate_fraction_at_risk')
    def test_alpha_model__get_signal(self, calculate_fraction_at_risk, calculate_exposure_mock):
        calculate_exposure_mock.return_value = Exposure.LONG
        calculate_fraction_at_risk.return_value = 3

        alpha_model = AlphaModel(risk_estimation_factor=4, data_provider=MagicMock())
        signal = alpha_model.get_signal(self.ticker, Exposure.OUT, self.end_time, self.frequency)

        expected_signal = Signal(self.ticker, Exposure.LONG, 3, Mock(), Mock(), alpha_model=alpha_model)
        self.assertEqual(signal, expected_signal)
