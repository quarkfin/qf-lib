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
from datetime import datetime
from typing import Union, Sequence, Optional

from numpy import nan
from pandas import concat
from pandas._libs.tslibs.offsets import to_offset
from pandas._libs.tslibs.timestamps import Timestamp

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider


class IntradayDataHandler(DataHandler):
    def __init__(self, data_provider: DataProvider, timer: Timer):
        super().__init__(data_provider, timer)
        self.default_frequency = data_provider.frequency if data_provider.frequency is not None else Frequency.MIN_1

    def _check_frequency(self, frequency):
        if frequency and frequency <= Frequency.DAILY:
            raise ValueError("Only frequency higher than daily is supported by IntradayDataHandler.")

    def _get_end_date_without_look_ahead(self, end_date: Optional[datetime], frequency: Frequency):
        """ If end_date is None, current time is taken as end_date. The function returns the end of latest full bar
        (get_price, get_history etc. functions always include the end_date e.g. in case of 1 minute frequency:
        current_time = 16:20 and end_date = 16:06 the latest returned bar is the [16:06, 16:07)).

        Examples:
        - current_time = 20:00, end_time = 17:01, frequency = 1h,
            => end_date_without_look_ahead = 17:00

        - current_time = 20:00, end_time = 19:58, frequency = 1h,
            => end_date_without_look_ahead = 19:00

        - current_time = 20:00, end_time = 20:01, frequency = 1h ,
            => end_date_without_look_ahead = 19:00

        - current_time = 20:00, end_time = 20:00, frequency = 1h,
            => end_date_without_look_ahead = 19

        - current_time = 20:10, end_time = 22:10, frequency = 1h,
            => end_date_without_look_ahead = 19

        - current_time = 19:58, end_time = 19:56 , frequency = 1m,
            => end_date_without_look_ahead = 19:56

        - current_time = 19:56, end_time = 19:58 , frequency = 1m,
            => end_date_without_look_ahead = 19:55
        """

        current_time = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_date = end_date or current_time
        end_date += RelativeDelta(second=0, microsecond=0)

        frequency_delta = to_offset(frequency.to_pandas_freq()).delta.value
        if current_time <= end_date:
            end_date_without_lookahead = Timestamp(math.floor(Timestamp(current_time).value / frequency_delta) *
                                                   frequency_delta).to_pydatetime() - frequency.time_delta()
        else:
            end_date_without_lookahead = Timestamp(math.floor(Timestamp(end_date).value / frequency_delta) *
                                                   frequency_delta).to_pydatetime()
        return end_date_without_lookahead

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None,
                                 end_time: Optional[datetime] = None) -> Union[float, QFSeries]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        if not tickers:
            return nan if got_single_ticker else PricesSeries()
        frequency = frequency or self.default_frequency
        current_time = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_time = end_time or current_time
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_time, frequency)

        if current_time <= end_time:
            last_prices = self.data_provider.get_last_available_price(tickers, frequency, end_date_without_look_ahead)
            current_open_prices = self.data_provider.get_price(tickers, PriceField.Open,
                                                               start_date=end_date_without_look_ahead + frequency.time_delta(),
                                                               end_date=end_date_without_look_ahead + frequency.time_delta(),
                                                               frequency=frequency)
        else:
            last_prices = self.data_provider.get_last_available_price(tickers, frequency, end_date_without_look_ahead - frequency.time_delta())
            current_open_prices = self.data_provider.get_price(tickers, PriceField.Open,
                                                               start_date=end_date_without_look_ahead,
                                                               end_date=end_date_without_look_ahead,
                                                               frequency=frequency)

        last_prices = concat([last_prices, current_open_prices], axis=1).ffill(axis=1)
        last_prices = last_prices.iloc[:, -1]

        return last_prices.iloc[0] if got_single_ticker else last_prices
