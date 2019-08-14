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

from qf_lib.backtesting.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.events.event_base import EventListener


class EmptyQueueEventListener(EventListener[EmptyQueueEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_empty_queue_event(self, event: EmptyQueueEvent):
        pass
