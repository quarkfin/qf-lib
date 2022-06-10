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
from datetime import datetime
from unittest import TestCase

import pandas as pd

from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.periods_list import periods_list_from_bool_series
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class TestPeriodsList(TestCase):
    def setUp(self):
        self.bool_series = QFSeries(
            data=[False, True, True, False, False, False, True, True, True],
            index=pd.DatetimeIndex(["2017-01-01", "2017-01-02", "2017-01-03", "2017-01-06", "2017-01-07",
                                    "2017-01-08", "2017-01-09", "2017-01-10", "2017-01-11"])
        )

    def test_periods_list_from_bool_series(self):
        actual_periods_list = periods_list_from_bool_series(self.bool_series)
        expected_periods_list = [
            (str_to_date("2017-01-02"), str_to_date("2017-01-06")),
            (str_to_date("2017-01-09"), str_to_date("2017-01-12"))
        ]
        assert_lists_equal(expected_periods_list, actual_periods_list)

        for start_date, end_date in actual_periods_list:
            self.assertEqual(datetime, type(start_date), "Error while checking start_date: {}".format(str(start_date)))
            self.assertEqual(datetime, type(end_date), "Error while checking end_date: {}".format(str(end_date)))


if __name__ == '__main__':
    unittest.main()
