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

from dateutil.relativedelta import relativedelta


class RelativeDelta(relativedelta):
    def __eq__(self, other):
        if other is self:
            return True

        if not isinstance(other, RelativeDelta):
            return False

        return (self.years, self.months, self.days, self.leapdays, self.hours, self.minutes, self.seconds,
                self.microseconds, self.year, self.month, self.day, self.weekday, self.hour, self.minute,
                self.second, self.microsecond) == \
            (other.years, other.months, other.days, other.leapdays, other.hours, other.minutes, other.seconds,
             other.microseconds, other.year, other.month, other.day, other.weekday, other.hour, other.minute,
             other.second, other.microsecond)

    def __hash__(self):
        return hash((self.years, self.months, self.days, self.leapdays, self.hours, self.minutes, self.seconds,
                     self.microseconds, self.year, self.month, self.day, self.weekday, self.hour, self.minute,
                     self.second, self.microsecond))
