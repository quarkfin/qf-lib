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

from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class RegularDateTimeRule:
    """
    RegularDateTimeRule is a helper class for TimeEvents. It has a convenience method for calculating
    next trigger time for events which occur on certain date/time on regular basis (e.g. each day at 9:30,
    each first day of a month, etc.).
    """

    def __init__(self, year: int = None, month: int = None, day: int = None, weekday: int = None, hour: int = None,
                 minute: int = None, second: int = None, microsecond: int = None):

        self.trigger_time = RelativeDelta(
            year=year, month=month, day=day, weekday=weekday, hour=hour, minute=minute,
            second=second, microsecond=microsecond
        )

    def next_trigger_time(self, now: datetime) -> datetime:
        next_trigger_time = now + self.trigger_time

        # check if next_trigger_time is in the past and if it is, it needs to be adjusted so that it's in the future
        if next_trigger_time <= now:
            next_trigger_time = self._get_next_trigger_time_after(next_trigger_time)

        return next_trigger_time

    def _get_next_trigger_time_after(self, start_time: datetime):
        # calculate proper adjustment (time shift):
        # if the month is important for the trigger time, than we should go to the next year
        # for getting the next occurrence, if it is unimportant but day is important,
        # then we should go to the next month etc.
        time_adjustment = None

        if self.trigger_time.year is not None:
            # nothing can be done if the year is important. No way of getting next occurrence (there will never be
            # the same year again)
            raise ArithmeticError(
                "Cannot get next occurrence of the event with `year` specified "
                "(there will never be the same year again)."
            )
        elif self.trigger_time.month is not None:
            time_adjustment = RelativeDelta(years=1)
        elif self.trigger_time.day is not None:
            time_adjustment = RelativeDelta(months=1)
        elif self.trigger_time.weekday is not None:
            time_adjustment = RelativeDelta(weeks=1)
        elif self.trigger_time.hour is not None:
            time_adjustment = RelativeDelta(days=1)
        elif self.trigger_time.minute is not None:
            time_adjustment = RelativeDelta(hours=1)
        elif self.trigger_time.second is not None:
            time_adjustment = RelativeDelta(minutes=1)
        elif self.trigger_time.microsecond is not None:
            time_adjustment = RelativeDelta(seconds=1)

        next_trigger_time = start_time + time_adjustment
        return next_trigger_time
