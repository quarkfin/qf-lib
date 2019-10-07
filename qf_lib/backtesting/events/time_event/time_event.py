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

from abc import abstractmethod, ABCMeta
from datetime import datetime

from qf_lib.backtesting.events.event_base import Event


class TimeEvent(Event, metaclass=ABCMeta):
    """
    Represents an event associated with certain date/time (e.g. 2017-05-13 13:00).
    """

    @abstractmethod
    def next_trigger_time(self, now: datetime) -> datetime:
        pass

    @abstractmethod
    def notify(self, listener) -> None:
        pass

    def __eq__(self, other):
        if self is other:
            return True

        if type(self) != type(other):
            return False

        return True

    def __hash__(self):
        return hash(type(self))
