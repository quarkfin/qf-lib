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

from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.portfolio.transaction import Transaction


class DummyMonitor(AbstractMonitor):

    def end_of_trading_update(self, timestamp: datetime = None):
        pass

    def end_of_day_update(self, timestamp: datetime):
        pass

    def real_time_update(self, timestamp: datetime):
        pass

    def record_transaction(self, transaction: Transaction):
        pass
