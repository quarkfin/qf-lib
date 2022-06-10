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
from datetime import datetime

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.data_providers.data_provider import DataProvider


class MovingAverageAlphaModel(AlphaModel):
    """
    This is an example of a simple AlphaModel. It applies two Exponential Moving Averages of different time periods
    on the recent market close prices of an asset to determine the suggested move. It suggests to go LONG on this asset
    if the shorter close prices moving average exceeds the longer one. Otherwise it suggests to go SHORT.
    """
    def __init__(self, fast_time_period: int, slow_time_period: int,
                 risk_estimation_factor: float, data_provider: DataProvider):
        super().__init__(risk_estimation_factor, data_provider)

        self.fast_time_period = fast_time_period
        self.slow_time_period = slow_time_period

        if fast_time_period < 3:
            raise ValueError('timeperiods shorter than 3 are pointless')
        if slow_time_period <= fast_time_period:
            raise ValueError('slow MA time period should be longer than fast MA time period')

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime,
                           frequency: Frequency) -> Exposure:
        num_of_bars_needed = self.slow_time_period
        close_tms = self.data_provider.historical_price(ticker, PriceField.Close, num_of_bars_needed,
                                                        current_time, frequency)

        fast_ma = close_tms.ewm(span=self.fast_time_period, adjust=False).mean()  # fast exponential moving average
        slow_ma = close_tms.ewm(span=self.slow_time_period, adjust=False).mean()  # slow exponential moving average

        if fast_ma[-1] > slow_ma[-1]:
            return Exposure.LONG
        else:
            return Exposure.SHORT

    def __hash__(self):
        return hash((self.__class__.__name__, self.fast_time_period, self.slow_time_period, self.risk_estimation_factor))
