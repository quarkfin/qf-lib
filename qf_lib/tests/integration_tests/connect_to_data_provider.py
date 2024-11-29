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
from typing import Optional

from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings


def get_data_provider(timer: Optional[Timer] = None):
    """
    Connects to Bloomberg data provider using the test settings.
    """
    settings = get_test_settings()
    bbg_provider = BloombergDataProvider(settings, timer)
    bbg_provider.connect()
    if not bbg_provider.connected:
        raise ConnectionError("No Bloomberg connection")

    return bbg_provider
