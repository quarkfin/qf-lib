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

from os.path import join

from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings


def get_test_settings() -> Settings:
    config_dir = join(get_src_root(), 'qf_lib', 'tests', 'unit_tests', 'config')
    test_settings_path = join(config_dir, 'test_settings.json')
    return Settings(test_settings_path)
