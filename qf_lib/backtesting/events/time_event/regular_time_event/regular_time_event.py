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

from abc import ABCMeta, abstractmethod

from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class RegularTimeEvent(TimeEvent, metaclass=ABCMeta):
    """ TimeEvent which occurs on regular basis (e.g. each day at 17:00). """

    @classmethod
    @abstractmethod
    def trigger_time(cls) -> RelativeDelta:
        """
        Returns the RelativeDelta which describes at what time the RegularTimeEvent occurs
        (e.g. RelativeDelta(hour=16, minute=0, second=0, microsecond=0) for an event which occurs every day at 16:00).
        """
        pass
