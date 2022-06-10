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

import os
import sys

from os.path import dirname, join

from qf_lib.get_sources_root import get_src_root

sys.path[0] = os.getcwd()  # dirty hack to make python interpreter know where to look for the modules to import


def main():
    from qf_lib.tests.helpers.run_tests_from_directory import run_tests_and_print_results
    tests_directory = join(dirname(__file__), "unit_tests")
    was_successful = run_tests_and_print_results(tests_directory, top_level_dir=get_src_root())
    sys.exit(not was_successful)


if __name__ == '__main__':
    main()
