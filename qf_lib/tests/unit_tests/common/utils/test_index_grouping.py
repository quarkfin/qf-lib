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
from unittest import TestCase

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.returns.index_grouping import get_grouping_for_frequency
from qf_lib.containers.series.qf_series import QFSeries


class TestIndexGrouping(TestCase):
    def setUp(self):
        self.index = pd.bdate_range(start='2014-12-15', end='2016-01-07')
        self.series = QFSeries(index=self.index, data=self.index)

    def test_daily_grouping(self):
        daily_grouping = get_grouping_for_frequency(Frequency.DAILY)
        actual_result = list(self.series.groupby(daily_grouping))

        day_ids, _ = zip(*actual_result)
        self.assertEqual(len(self.index), len(day_ids))

    def test_weekly_grouping(self):
        weekly_grouping = get_grouping_for_frequency(Frequency.WEEKLY)
        actual_result = list(self.series.groupby(weekly_grouping))

        # first week should contain everything up to 2014-12-28 and should belong to the last week of the 2014
        week_id, series = actual_result[0]
        self.assertEqual((2014, 51), week_id)
        self.assertEqual(series.min(), str_to_date("2014-12-15"))
        self.assertEqual(series.max(), str_to_date("2014-12-19"))

        week_id, series = actual_result[1]
        self.assertEqual((2014, 52), week_id)
        self.assertEqual(series.min(), str_to_date("2014-12-22"))
        self.assertEqual(series.max(), str_to_date("2014-12-26"))

        # dates from range 2014-12-29 to 2015-01-04 should be in the same week
        week_id, series = actual_result[2]
        self.assertEqual((2015, 1), week_id)
        self.assertEqual(series.min(), str_to_date("2014-12-29"))
        self.assertEqual(series.max(), str_to_date("2015-01-02"))

    def test_monthly_grouping(self):
        monthly_grouping = get_grouping_for_frequency(Frequency.MONTHLY)
        actual_result = list(self.series.groupby(monthly_grouping))

        month_id, series = actual_result[0]
        self.assertEqual(month_id, (2014, 12))
        self.assertEqual(series.min(), str_to_date("2014-12-15"))
        self.assertEqual(series.max(), str_to_date("2014-12-31"))

        month_id, series = actual_result[1]
        self.assertEqual(month_id, (2015, 1))
        self.assertEqual(series.min(), str_to_date("2015-01-01"))
        self.assertEqual(series.max(), str_to_date("2015-01-30"))

        month_id, series = actual_result[-1]
        self.assertEqual(month_id, (2016, 1))
        self.assertEqual(series.min(), str_to_date("2016-01-01"))
        self.assertEqual(series.max(), str_to_date("2016-01-07"))

        self.assertEqual(14, len(actual_result))

    def test_yearly_grouping(self):
        yearly_grouping = get_grouping_for_frequency(Frequency.YEARLY)
        actual_result = list(self.series.groupby(yearly_grouping))

        year, series = actual_result[0]
        self.assertEqual(year, 2014)
        self.assertEqual(series.min(), str_to_date("2014-12-15"))
        self.assertEqual(series.max(), str_to_date("2014-12-31"))

        year, series = actual_result[1]
        self.assertEqual(year, 2015)
        self.assertEqual(series.min(), str_to_date("2015-01-01"))
        self.assertEqual(series.max(), str_to_date("2015-12-31"))

        year, series = actual_result[2]
        self.assertEqual(year, 2016)
        self.assertEqual(series.min(), str_to_date("2016-01-01"))
        self.assertEqual(series.max(), str_to_date("2016-01-07"))


if __name__ == '__main__':
    unittest.main()
