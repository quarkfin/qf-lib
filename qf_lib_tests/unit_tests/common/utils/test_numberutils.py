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

from unittest import TestCase

import numpy as np

from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


class TestNumberUtils(TestCase):
    def test_is_finite_number(self):
        self.assertFalse(is_finite_number(None))
        self.assertFalse(is_finite_number("There is a bomb attack on US president being planned"))
        self.assertFalse(is_finite_number(np.inf))
        self.assertFalse(is_finite_number(np.nan))
        self.assertFalse(is_finite_number(self))
        self.assertTrue(is_finite_number(2.5))
