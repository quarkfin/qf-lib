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

from qf_lib.backtesting.events.time_event.regular_time_event.regular_market_event import RegularMarketEvent


class AfterMarketCloseEvent(RegularMarketEvent):
    """
    Rule which is triggered every day after market closes.
    For example in order to set up 23:30 call before using the event:
    ``BeforeMarketOpenEvent.set_trigger_time({"hour": 23, "minute": 30, "second": 0, "microsecond": 0})``

    The listeners for this event should implement the ``on_after_market_close()`` method.
    """

    def notify(self, listener) -> None:
        listener.on_after_market_close(self)
