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

from qf_lib.backtesting.events.time_event.regular_date_time_rule import RegularDateTimeRule
from qf_lib.backtesting.events.time_event.regular_time_event import RegularTimeEvent
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class MarketOpenEvent(RegularTimeEvent):
    """
    Rule which is triggered every day when the market opens (9:30 AM for NASDAQ and NYSE).

    The listeners for this event should implement the on_market_open() method.
    """

    _trigger_time = {"hour": 9, "minute": 30, "second": 0, "microsecond": 0}
    _trigger_time_rule = RegularDateTimeRule(**_trigger_time)

    @classmethod
    def trigger_time(cls) -> RelativeDelta:
        return RelativeDelta(**cls._trigger_time)

    @classmethod
    def next_trigger_time(cls, now: datetime) -> datetime:
        next_trigger_time = cls._trigger_time_rule.next_trigger_time(now)
        return next_trigger_time

    def notify(self, listener) -> None:
        listener.on_market_open(self)
