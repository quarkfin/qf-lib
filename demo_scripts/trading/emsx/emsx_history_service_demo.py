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

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.settings import Settings
from qf_lib.trading.emsx.emsx_history_service import EMSXHistoryService


def main():
    """
    Requires emsx configuration in the settings file. Necessary fields are:
    - host (IP address or 'localhost')
    - port (default port for Bloomberg is 8194)
    - username
    - uuid
    - local (true or false)
    - local_tz (e.g. 'Europe/Zurich')
    - test (true or false to know if the testing framework should be used)
    """
    settings = container.resolve(Settings)
    emsx_service = EMSXHistoryService(settings)
    emsx_service.connect()

    fills = emsx_service.get_fills(start_date=datetime.now() - RelativeDelta(days=10))
    for fill in fills:
        print(fill)
