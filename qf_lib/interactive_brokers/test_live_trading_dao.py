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
from data_providers.db_connection_provider import ReadWriteDBConnectionDevelopment
from data_providers.internal_db.live_trading.live_trading_dao import LiveTradingDAO
from qf_common.config.ioc import container
from qf_lib.common.utils.dateutils.string_to_date import str_to_date

db_connection_provider = container.resolve(ReadWriteDBConnectionDevelopment)

dao = LiveTradingDAO(db_connection_provider)
print(dao.get_open_orders())
for t in dao.get_transactions(str_to_date("2021-10-06")):
    print(t)