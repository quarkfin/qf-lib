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

import unittest


def run_tests_and_print_results(tests_directory, top_level_dir):
    """
    Runs tests from the given directory and prints the results on the console.

    Returns
    -------
    True if all tests passed successfully; False - otherwise
    """
    result = run_tests(tests_directory, top_level_dir)
    skipped_tests_messsage = get_skipped_messages_info(result)
    print(skipped_tests_messsage)

    return result.wasSuccessful()


def run_tests(tests_directory, top_level_dir):
    suite = unittest.TestLoader().discover(start_dir=tests_directory, top_level_dir=top_level_dir)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return result


def get_skipped_messages_info(result):
    skipped_info_list = ["Skipped tests:"]
    for skipped_cls, message in result.skipped:
        skipped_test_info = "[{cls_name:s}] {message:s}".format(
            cls_name=skipped_cls.__class__.__name__,
            message=message
        )
        skipped_info_list.append(skipped_test_info)

    skipped_tests_messsage = "\n".join(skipped_info_list)

    return skipped_tests_messsage
