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


class CalculateAndPlaceOrdersRegularEvent(RegularMarketEvent):
    """
    Class implementing the logic for all triggering regular calculation of signals and placing orders.
    This should be used as a trigger for a a strategy to run calculations.

    Example:
        trigger_time {"hour": 13, "minute": 30, "second": 0, "microsecond": 0}
        CalculateAndPlaceOrdersRegularEvent.set_trigger_time(trigger_time)
        will result in an event being triggered every day at 13:30

        trigger_time {"minute": 5, "second": 0, "microsecond": 0}
        CalculateAndPlaceOrdersRegularEvent.set_trigger_time(trigger_time)
        will result in an event being triggered every hour, 00:05, 01:05, 02:05, ...
    """

    _timer = None

    def notify(self, listener) -> None:
        listener.calculate_and_place_orders()

    @classmethod
    def set_daily_default_trigger_time(cls):
        """
        Convenience method used to set daily trigger time at 1:00 a.m. every day.
        This causes the signals to be calculated every day (in case if exclude_weekends() was not called, on working
        days otherwise) early in the morning.
        """
        cls.set_trigger_time({"hour": 1, "minute": 0, "second": 0, "microsecond": 0})
