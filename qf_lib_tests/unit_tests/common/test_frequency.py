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

from pandas import DatetimeIndex

from qf_lib.common.enums.frequency import Frequency


class TestFrequency(TestCase):
    def test_from_string(self):
        self.assertEqual(Frequency.DAILY, Frequency.from_string('daily'))
        self.assertEqual(Frequency.WEEKLY, Frequency.from_string('weekly'))
        self.assertEqual(Frequency.MONTHLY, Frequency.from_string('monthly'))
        self.assertEqual(Frequency.QUARTERLY, Frequency.from_string('quarterly'))
        self.assertEqual(Frequency.SEMI_ANNUALLY, Frequency.from_string('semi_annually'))
        self.assertEqual(Frequency.YEARLY, Frequency.from_string('yearly'))

    def test_get_lowest(self):
        self.assertEqual(Frequency.get_lowest_freq({"A": Frequency.DAILY, "B": Frequency.WEEKLY, "C": Frequency.YEARLY}),
                         "C")
        self.assertEqual(Frequency.get_lowest_freq({"A": Frequency.DAILY, "B": Frequency.WEEKLY, "C": Frequency.MONTHLY}),
                         "C")
        self.assertEqual(Frequency.get_lowest_freq({"A": Frequency.DAILY}),
                         "A")

    def test_infer(self):
        index = DatetimeIndex(['2015-01-02T00:00:00.000000000', '2015-01-05T00:00:00.000000000',
                               '2015-01-06T00:00:00.000000000', '2015-01-07T00:00:00.000000000',
                               '2015-01-08T00:00:00.000000000', '2015-01-09T00:00:00.000000000',
                               '2015-01-12T00:00:00.000000000', '2015-01-13T00:00:00.000000000',
                               '2015-01-14T00:00:00.000000000', '2015-01-15T00:00:00.000000000',
                               '2015-01-16T00:00:00.000000000', '2015-01-20T00:00:00.000000000',
                               '2015-01-21T00:00:00.000000000', '2015-01-22T00:00:00.000000000',
                               '2015-01-23T00:00:00.000000000', '2015-01-26T00:00:00.000000000',
                               '2015-01-27T00:00:00.000000000', '2015-01-28T00:00:00.000000000'])
        self.assertEqual(Frequency.infer_freq(index), Frequency.DAILY)

        index = DatetimeIndex(['2015-01-31T00:00:00.000000000', '2015-02-28T00:00:00.000000000',
                               '2015-03-31T00:00:00.000000000', '2015-04-30T00:00:00.000000000',
                               '2015-05-31T00:00:00.000000000', '2015-06-30T00:00:00.000000000',
                               '2015-07-31T00:00:00.000000000', '2015-08-31T00:00:00.000000000',
                               '2015-09-30T00:00:00.000000000', '2015-10-31T00:00:00.000000000',
                               '2015-11-30T00:00:00.000000000', '2015-12-31T00:00:00.000000000',
                               '2016-01-31T00:00:00.000000000', '2016-02-29T00:00:00.000000000',
                               '2016-03-31T00:00:00.000000000', '2016-04-30T00:00:00.000000000',
                               '2016-05-31T00:00:00.000000000', '2016-06-30T00:00:00.000000000',
                               '2016-07-31T00:00:00.000000000', '2016-08-31T00:00:00.000000000',
                               '2016-09-30T00:00:00.000000000', '2016-10-31T00:00:00.000000000',
                               '2016-11-30T00:00:00.000000000', '2016-12-31T00:00:00.000000000'])
        self.assertEqual(Frequency.infer_freq(index), Frequency.MONTHLY)

        index = DatetimeIndex(['2015-01-31T00:00:00.000000000', '2015-02-28T00:00:00.000000000',
                               '2015-04-30T00:00:00.000000000',
                               '2015-05-31T00:00:00.000000000', '2015-06-30T00:00:00.000000000',
                               '2015-07-31T00:00:00.000000000', '2015-08-31T00:00:00.000000000'])
        self.assertEqual(Frequency.infer_freq(index), Frequency.MONTHLY)
