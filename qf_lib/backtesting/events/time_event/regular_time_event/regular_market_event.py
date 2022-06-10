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
from abc import ABCMeta
from datetime import datetime
from typing import Dict

from qf_lib.backtesting.events.time_event.regular_date_time_rule import RegularDateTimeRule
from qf_lib.backtesting.events.time_event.regular_time_event.regular_time_event import RegularTimeEvent
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class RegularMarketEvent(RegularTimeEvent, metaclass=ABCMeta):
    """
    Class implementing the logic for all events happening every day such as MarketOpenEvent, MarketCloseEvent etc.
    The time has to be set up by calling ``set_trigger_time`` before being able to run the backtest.
    """

    _trigger_time = None   # type: Dict[str, int]
    # for ex: {"hour": 13, "minute": 30, "second": 0, "microsecond": 0}
    _trigger_time_rule = None  # type: RegularDateTimeRule

    _run_over_weekends: bool = True

    @classmethod
    def set_trigger_time(cls, trigger_time_dict: Dict[str, int]):
        cls._trigger_time = trigger_time_dict
        cls._trigger_time_rule = RegularDateTimeRule(**trigger_time_dict)

    @classmethod
    def trigger_time(cls) -> RelativeDelta:
        if cls._trigger_time is None:
            raise ValueError("set up the trigger time by calling set_trigger_time() before using the event")

        return RelativeDelta(**cls._trigger_time)

    def next_trigger_time(self, now: datetime) -> datetime:
        if self._trigger_time_rule is None:
            raise ValueError("set up the trigger time by calling set_trigger_time() before using the event")

        next_trigger_time = self._trigger_time_rule.next_trigger_time(now)
        while not self._run_over_weekends and next_trigger_time.weekday() in (5, 6):
            next_trigger_time = self._trigger_time_rule.next_trigger_time(next_trigger_time)

        return next_trigger_time

    @classmethod
    def exclude_weekends(cls):
        """ If called, the calculate_and_place_orders will not be notified over the weekends. """
        cls._run_over_weekends = False
