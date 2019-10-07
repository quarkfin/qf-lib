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
from typing import Optional, Dict, Any

from qf_lib.backtesting.events.time_event.time_event import TimeEvent


class SingleTimeEvent(TimeEvent):
    """
    SingleTimeEvent class represents all events associated with one specific date time (e.g. 2017-05-13 13:00),
    which will never be repeated in the future.

    This type of events is mostly used along with data being passed between different components. In order to schedule
    new single time event, schedule_new_event function should be used. This will add a predefined datetime parameter
    along with necessary data to the _datetimes_to_data dictionary.

    SingleTimeEvent uses a class method for new events scheduling and a static dictionary _datetimes_to_data, as
    Scheduler requires types of events in subscription function (the listener subscribes to type of time event,
    represented usually by a class, not to a certain time event object).
    """

    _datetimes_to_data = {}  # type: Dict[datetime, Any]

    @classmethod
    def schedule_new_event(cls, date_time: datetime, data: Any):
        """
        Schedules new event by adding the (date_time, data) pair to the _datetimes_to_data dictionary.
        By default the SingleTimeEvent raises ValueError if an event is already scheduled for this particular date time.

        Parameters
        ----------
        date_time
            datetime representing the specific scheduled time, when the event will occur
        data
            data that may be passed with the event
        """
        if date_time not in cls._datetimes_to_data.keys():
            cls._datetimes_to_data[date_time] = data
        else:
            raise ValueError("Event associated with the given datetime has been already scheduled.")

    def next_trigger_time(self, now: datetime) -> Optional[datetime]:
        """
        Returns the time of next scheduled event or None, if no event exists in the future.
        """
        date_times = list(self._datetimes_to_data.keys())
        for date_time in date_times:
            if date_time <= now:
                del self._datetimes_to_data[date_time]
        return min(self._datetimes_to_data) if self._datetimes_to_data else None

    def notify(self, listener) -> None:
        """
        Notifies the listener and deletes the event from the dictionary.
        """
        listener.on_single_time_event(self)

    @classmethod
    def get_data(cls, time: datetime):
        """
        For an initialized object representing a certain single time event, returns the data associated with this event.
        """
        return cls._datetimes_to_data[time]

    @classmethod
    def clear(cls):
        cls._datetimes_to_data.clear()
