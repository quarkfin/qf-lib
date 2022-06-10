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
from qf_lib.backtesting.events.time_event.periodic_event.periodic_event import PeriodicEvent


class CalculateAndPlaceOrdersPeriodicEvent(PeriodicEvent):
    """
    Class used for triggering calculation of signals and placing orders.
    Alternative class to do it is CalculateAndPlaceOrdersRegularEvent
    This should be used as a trigger for a a strategy to run calculations.

    Example:
        CalculateAndPlaceOrdersPeriodicEvent.set_frequency(Frequency.MIN_15)
        CalculateAndPlaceOrdersPeriodicEvent.set_start_and_end_time(
            start_time={"hour": 8, "minute": 0, "second": 0, "microsecond": 0},
            end_time={"hour": 16, "minute": 30, "second": 0, "microsecond": 0})
        will results in notifier being triggered at 8:00, 8:15, 8:30, ..., 16:15
    """

    def notify(self, listener) -> None:
        listener.calculate_and_place_orders()
