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

import sys


def get_function_name(parent_idx=0) -> str:
    """
    While called inside a function or a class method it returns the name of the function/method that called it as a
    string. For example inside method_a() definition, the get_function_name() returns 'method_a'.
    """
    return sys._getframe(1 + parent_idx).f_code.co_name
