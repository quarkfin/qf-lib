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
#

import datetime
from typing import Dict

from qf_lib.backtesting.events.time_event.periodic_event.periodic_event import PeriodicEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class IntradayBarEvent(PeriodicEvent):
    """
    Periodic events used mostly by the SimulatedExecutionHandler to organize the Order Executors operation.
    It calls on_new_bar function on the listener at every trigger time between start_time and end_time, which denote
    the time range between market open (exclusive) and market close (exclusive).

    The listener is not notified at market open and market close events.
    """

    def __init__(self):
        self.frequency = Frequency.MIN_1
        self.start_time = self._shift_time(MarketOpenEvent._trigger_time, self.frequency.time_delta())
        self.end_time = self._shift_time(MarketCloseEvent._trigger_time, -self.frequency.time_delta())

        super().__init__()

    def notify(self, listener) -> None:
        listener.on_new_bar(self)

    def _shift_time(self, time_dict: Dict, time_delta: RelativeDelta):
        """
        Helper function, which allows to add time (RelativeDelta) to a time dictionary, which may contain the following
        fields: "hour", "minute", "second", "microsecond".

        E.g. for time_dict = {"hour": 13, "minute": 30} and time_delta = RelativeDelta(minutes=-10) the result would be as
        follows: {"hour": 13, "minute": 20}.
        """

        now = datetime.datetime.now()
        time = now + RelativeDelta(**time_dict) + time_delta
        base_time = now + RelativeDelta(hour=0, minute=0, second=0, microsecond=0)
        delta = RelativeDelta(time, base_time)

        # Create a dictionary containing absolute parameters (hour, minute etc) instead of relative ones (hours, minutes
        # etc) and assign corresponding values from _delta.

        def absolute_to_relative(field_name):
            # The only difference between absolute and relative values is the change from singular to plural
            return "{}s".format(field_name)

        result_time_dict = {
            key: getattr(delta, absolute_to_relative(key)) for key in time_dict.keys()
        }

        return result_time_dict
