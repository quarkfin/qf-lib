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
from typing import Optional, Union, Sequence, Type

from numpy import nan
from pandas import concat

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.regular_market_event import RegularMarketEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider


class DailyDataHandler(DataHandler):
    def __init__(self, data_provider: DataProvider, timer: Timer):
        super().__init__(data_provider, timer)
        self.default_frequency = data_provider.frequency if data_provider.frequency is not None else Frequency.DAILY

    def _check_frequency(self, frequency):
        if frequency and frequency > Frequency.DAILY:
            raise ValueError("Frequency higher than daily is not supported by DailyDataHandler.")

    def _get_end_date_without_look_ahead(self, end_date: Optional[datetime], frequency: Frequency):
        """ Points always to the latest market close for which the data could be retrieved. """
        return self._get_last_available_market_event(end_date, MarketCloseEvent)

    def _get_last_available_market_event(self, end_date: Optional[datetime], event: Type[RegularMarketEvent]):
        current_datetime = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_date = end_date or current_datetime
        end_date += RelativeDelta(days=1, hour=0, minute=0, second=0, microsecond=0, microseconds=-1)

        today_market_event = current_datetime + event.trigger_time()
        yesterday_market_event = today_market_event - RelativeDelta(days=1)
        latest_available_market_event = yesterday_market_event if current_datetime < today_market_event \
            else today_market_event

        latest_market_event = min(latest_available_market_event, end_date)
        return datetime(latest_market_event.year, latest_market_event.month, latest_market_event.day)

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None,
                                 end_time: Optional[datetime] = None) -> Union[float, QFSeries]:
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        if not tickers:
            return nan if got_single_ticker else PricesSeries()

        frequency = frequency or self.default_frequency
        end_time = end_time or self.timer.now()
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_time, frequency)

        last_prices = self.data_provider.get_last_available_price(tickers, frequency, end_date_without_look_ahead)

        latest_market_open = self._get_last_available_market_event(end_time, MarketOpenEvent)
        if end_date_without_look_ahead < latest_market_open:

            current_open_prices = self.data_provider.get_price(tickers, PriceField.Open, latest_market_open,
                                                               latest_market_open, frequency)
            last_prices = concat([last_prices, current_open_prices], axis=1).ffill(axis=1)
            last_prices = last_prices.iloc[:, -1]

        return last_prices.iloc[0] if got_single_ticker else last_prices
