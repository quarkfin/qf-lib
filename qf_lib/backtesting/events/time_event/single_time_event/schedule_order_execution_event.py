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

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from qf_lib.backtesting.events.time_event.single_time_event.single_time_event import SingleTimeEvent
from qf_lib.backtesting.execution_handler.simulated_executor import SimulatedExecutor
from qf_lib.backtesting.order.order import Order


class ScheduleOrderExecutionEvent(SingleTimeEvent):

    _datetimes_to_data = defaultdict(lambda: defaultdict(list))  # type: Dict[datetime, Dict[SimulatedExecutor, List[Order]]]

    @classmethod
    def schedule_new_event(cls, date_time: datetime, executor_to_orders_dict: Dict[SimulatedExecutor, List[Order]]):
        """
        Schedules new event by adding the (date_time, data) pair to the _datetimes_to_data dictionary.

        It assumes data has the structure of a dictionary, which maps orders executor instance to orders, which need
        to be executed.

        Multiple events can be scheduled for the same time - the orders and order executors will be appended to
        existing data.
        """
        for order_executor in executor_to_orders_dict.keys():
            cls._datetimes_to_data[date_time][order_executor].extend(executor_to_orders_dict[order_executor])

    def notify(self, listener) -> None:
        """
        Notifies the listener.
        """
        listener.on_orders_accept(self)

    @classmethod
    def get_executors_to_orders_dict(cls, time: datetime) -> Dict[SimulatedExecutor, List[Order]]:
        """
        For an initialized object representing a certain single time event, returns the data associated with this event
        in the form of a dictionary, with SimulatedExecutor as keys and list of Orders as values.
        """
        return cls._datetimes_to_data[time]
