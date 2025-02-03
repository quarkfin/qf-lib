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
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union, Sequence, Type, Set, Optional

from pandas import Timestamp, Timedelta

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.regular_market_event import RegularMarketEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer, RealTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries


class DataProvider(metaclass=ABCMeta):
    """ An interface for data providers (for example AbstractPriceDataProvider). """

    frequency = None

    def __init__(self, timer: Optional[Timer] = None):
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.timer = timer or RealTimer()

    def set_timer(self, timer: Timer):
        self.timer = timer

    def set_frequency(self, frequency):
        self.frequency = frequency

    @abstractmethod
    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, frequency: Frequency = None, look_ahead_bias: bool = False,
            **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical attributes (fields) of different securities (tickers).

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            tickers for securities which should be retrieved
        fields: None, str, Sequence[str]
            fields of securities which should be retrieved.
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        frequency: Frequency
            frequency of the data
        look_ahead_bias: bool
            if set to False, the look-ahead bias will be taken care of to make sure no future data is returned
        kwargs
            kwargs should not be used on the level of AbstractDataProvider. They are here to provide a common interface
            for all data providers since some of the specific data providers accept additional arguments

        Returns
        -------
        QFSeries, QFDataFrame, QFDataArray, float, str
            If possible the result will be squeezed, so that instead of returning a QFDataArray, data of lower
            dimensionality will be returned. The results will be either a QFDataArray (with 3 dimensions: date, ticker,
            field), a QFDataFrame (with 2 dimensions: date, ticker or field; it is also possible to get 2 dimensions
            ticker and field if single date was provided), a QFSeries (with 1 dimensions: date) or a float / str
            (in case if a single ticker, field and date were provided).
            If no data is available in the database or a non existing ticker was provided an empty structure
            (nan, QFSeries, QFDataFrame or QFDataArray) will be returned.
        """
        pass

    @abstractmethod
    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        """
        Returns classes of tickers which are supported by this DataProvider.
        """
        pass

    def get_end_date_without_look_ahead(self, end_date: Optional[datetime], frequency: Frequency):
        end_date = end_date or self.timer.now()
        end_date = end_date + RelativeDelta(second=0, microsecond=0)
        if isinstance(self.timer, RealTimer):
            return end_date

        frequency = frequency or self.frequency
        if frequency <= Frequency.DAILY:
            return self._get_last_available_market_event(end_date, MarketCloseEvent)
        else:
            return self._get_end_date_without_look_ahead_intraday(end_date, frequency)

    def _get_last_available_market_event(self, end_date: Optional[datetime], event: Type[RegularMarketEvent]):
        current_datetime = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_date = end_date or current_datetime
        end_date += RelativeDelta(days=1, hour=0, minute=0, second=0, microsecond=0, microseconds=-1)

        today_market_event = current_datetime + event.trigger_time()
        yesterday_market_event = today_market_event - RelativeDelta(days=1)
        latest_available_market_event = yesterday_market_event if current_datetime < today_market_event \
            else today_market_event

        latest_market_event = min(latest_available_market_event, end_date)
        return latest_market_event

    def _get_end_date_without_look_ahead_intraday(self, end_date: Optional[datetime], frequency: Frequency):
        """
        If end_date is None, current time is taken as end_date. The function returns the end of latest full bar
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

        frequency_delta = Timedelta((current_time + frequency.time_delta()) - current_time).value
        if current_time <= end_date:
            end_date_without_lookahead = Timestamp(math.floor(Timestamp(current_time).value / frequency_delta) *
                                                   frequency_delta).to_pydatetime() - frequency.time_delta()
        else:
            end_date_without_lookahead = Timestamp(math.floor(Timestamp(end_date).value / frequency_delta) *
                                                   frequency_delta).to_pydatetime()
        return end_date_without_lookahead

    def __str__(self):
        return self.__class__.__name__
