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

import abc
from datetime import datetime


class Timer:
    """
    Timer object which is a component in IOC. Used for getting information about time.
    """

    @abc.abstractmethod
    def now(self) -> datetime:
        pass


class RealTimer(Timer):
    """
    Timer which gives the real current time.
    """

    def now(self) -> datetime:
        return datetime.now()


class SettableTimer(Timer):
    """
    Timer object which doesn't give the real current time, but is "faking" it (current time can be set).
    """

    def __init__(self, initial_time: datetime = None):
        self.time = initial_time

    def now(self) -> datetime:
        return self.time

    def set_current_time(self, time: datetime):
        self.time = time
