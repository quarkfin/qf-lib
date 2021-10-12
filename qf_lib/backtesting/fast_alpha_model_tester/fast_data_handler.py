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
from typing import Union, Sequence, Optional

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.data_providers.data_provider import DataProvider


class FastDataHandler(DataHandler):
    """
    Class pretending to be a DataHandler but being much faster and not protecting from the look-ahead bias (one needs
    to be careful).
    """

    def __init__(self, data_provider: DataProvider, timer: Timer, default_frequency: Frequency = Frequency.DAILY):
        super().__init__(data_provider, timer)
        self._default_frequency = default_frequency

    def historical_price(self, ticker, fields, num_of_bars_needed, end_date: Optional[datetime] = None,
                         frequency: Frequency = Frequency.DAILY):
        end_date = self.timer.now() if end_date is None else end_date
        start_date = end_date - 2 * RelativeDelta(days=num_of_bars_needed)
        too_much_of_data = self.data_provider.get_price(ticker, fields, start_date, end_date,
                                                        frequency)  # type: PricesDataFrame
        result = too_much_of_data.tail(num_of_bars_needed)
        return result

    def _check_frequency(self, frequency):
        pass

    def _get_end_date_without_look_ahead(self, end_date: datetime = None):
        return end_date

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]], start_date: datetime,
            end_date: datetime = None, frequency: Frequency = None, **kwargs):
        raise NotImplementedError("FastDataHandler does not currently support get_history() function")

    def get_last_available_price(self, ickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None,
                                 end_time: Optional[datetime] = None):
        raise NotImplementedError("FastDataHandler does not currently support get_last_available_price() function")
