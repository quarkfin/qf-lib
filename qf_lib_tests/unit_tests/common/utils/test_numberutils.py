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
