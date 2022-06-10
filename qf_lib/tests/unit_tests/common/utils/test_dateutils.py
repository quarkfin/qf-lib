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

import datetime
import unittest
from unittest import TestCase

import pandas as pd

from qf_lib.common.utils.dateutils.common_start_and_end import get_common_start_and_end
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.dateutils.eom_date import eom_date
from qf_lib.common.utils.dateutils.get_quarter import get_quarter
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class TestDateUtils(TestCase):
    def test_str_to_date(self):
        expected_date = datetime.datetime(year=2000, month=11, day=30)
        actual_date = str_to_date('2000-11-30')
        self.assertEqual(actual_date, expected_date)

    def test_date_to_str(self):
        expected_str = '2000-11-30'
        actual_date = date_to_str(datetime.datetime(year=2000, month=11, day=30))
        self.assertEqual(actual_date, expected_str)

    def test_eomdate(self):
        expected_date = datetime.datetime(year=2016, month=2, day=29)

        some_day_in_february_2016 = datetime.datetime(year=2016, month=2, day=14)
        actual_date = eom_date(date=some_day_in_february_2016)
        self.assertEqual(actual_date, expected_date)

        actual_date2 = eom_date(year=2016, month=2)
        self.assertEqual(actual_date2, expected_date)

    def test_get_quarter(self):
        self.assertEqual(get_quarter(datetime.datetime(year=2016, month=1, day=1)), 1)
        self.assertEqual(get_quarter(datetime.datetime(year=2005, month=4, day=1)), 2)
        self.assertEqual(get_quarter(datetime.datetime(year=1994, month=7, day=1)), 3)
        self.assertEqual(get_quarter(datetime.datetime(year=2000, month=12, day=1)), 4)

    def test_get_common_start_and_end(self):
        index = pd.DatetimeIndex([
            "2015-01-01", "2015-02-01", "2015-03-01", "2015-04-01", "2015-05-01", "2015-06-01", "2015-07-01",
            "2015-08-01", "2015-09-01"
        ])
        columns = pd.Index(['a', 'b'])
        data = [
            [None, None],
            [1.1, None],
            [None, None],
            [1.2, None],
            [1.5, 1.2],
            [1.6, 1.9],
            [1.3, None],
            [1.2, 3.0],
            [None, 1.1]
        ]
        test_dataframe = QFDataFrame(data, index, columns)
        actual_common_start, actual_common_end = get_common_start_and_end(test_dataframe)
        expected_common_start = str_to_date("2015-05-01")
        expected_common_end = str_to_date("2015-08-01")
        self.assertEqual(actual_common_start, expected_common_start)
        self.assertEqual(actual_common_end, expected_common_end)


if __name__ == "__main__":
    unittest.main()
