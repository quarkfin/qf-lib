import unittest
from unittest import TestCase

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.index_grouping import get_grouping_for_frequency


class TestIndexGrouping(TestCase):
    def setUp(self):
        pass

    def test_get_grouping_for_frequency(self):
        index = pd.date_range(start='2000-12-20', end='2018-01-03', freq='D')
        data = index.year
        series = pd.Series(data, index)

        grouping = get_grouping_for_frequency(Frequency.WEEKLY)
        actual_result = series.groupby(grouping)
        print(actual_result)


if __name__ == '__main__':
    unittest.main()
