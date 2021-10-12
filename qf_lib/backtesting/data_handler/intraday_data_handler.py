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

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.data_providers.data_provider import DataProvider


class IntradayDataHandler(DataHandler):
    def __init__(self, data_provider: DataProvider, timer: Timer):
        super().__init__(data_provider, timer)
        self.default_frequency = data_provider.frequency if data_provider.frequency is not None else Frequency.MIN_1

    def _check_frequency(self, frequency):
        if frequency and frequency <= Frequency.DAILY:
            raise ValueError("Only frequency higher than daily is supported by IntradayDataHandler.")

    def _get_end_date_without_look_ahead(self, end_date: datetime = None):
        """
        Consider only the meaningful part of the date time (as the data can be gather at most with minutely
        frequency, delete the seconds and microseconds time part). Moreover, the `end date` is always exclusive,
        therefore it is only necessary to get the minimum of current time and the end date.
        If end_date is None, it is assumed that it is equal to current time.
        """

        current_time = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_date = end_date + RelativeDelta(second=0, microsecond=0) if end_date is not None else current_time

        return min(current_time, end_date)
