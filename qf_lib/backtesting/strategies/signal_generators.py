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
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.strategies.abstract_strategy import AbstractStrategy


class OnBeforeMarketOpenSignalGeneration:
    """
    Wrapper, which facilitates the subscription process of the Strategy to the BeforeMarketOpenEvent.
    After the creation of a strategy object, in order to proceed with the signal generation and orders placement
    every day at the BeforeMarketOpenEvent, it is necessary to encapsulate the strategy in the following way:

    strategy = ExampleStrategy(trading_session)
    OnBeforeMarketOpenSignalGeneration(strategy)

    This will ensure, that every day (from Monday to Friday) before the market open time, the calculate_and_place_orders
    will be executed.

    It requires the trigger_time of the BeforeMarketOpenEvent event to be set properly set, by calling the
    ``set_trigger_time`` function before using the OnBeforeMarketOpenSignalGeneration.
    """
    def __init__(self, strategy: AbstractStrategy):
        self.strategy = strategy
        self.timer = strategy.timer
        strategy.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        if self.timer.now().weekday() not in (5, 6):  # Skip saturdays and sundays
            self.strategy.calculate_and_place_orders()
