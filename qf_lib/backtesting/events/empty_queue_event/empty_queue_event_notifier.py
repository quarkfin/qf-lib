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

from typing import Type

from qf_lib.backtesting.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.events.empty_queue_event.empty_queue_event_listener import EmptyQueueEventListener
from qf_lib.backtesting.events.event_base import EventNotifier, AllEventNotifier


class EmptyQueueEventNotifier(EventNotifier[EmptyQueueEvent, EmptyQueueEventListener]):
    def __init__(self, event_notifier: AllEventNotifier) -> None:
        super().__init__()
        self.event_notifier = event_notifier

    def notify_all(self, event: EmptyQueueEvent):
        self.event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_empty_queue_event(event)

    @classmethod
    def events_type(cls) -> Type[EmptyQueueEvent]:
        return EmptyQueueEvent
