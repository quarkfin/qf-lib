import unittest
import warnings

import pandas as pd

from qf_lib.common.utils.dataframe.apply_to_column_groups import apply_to_column_groups


class _Ticker:
    def __init__(self, name: str, suffix: str):
        self.name = name
        self.suffix = suffix

    def __repr__(self):
        return f"{self.name}-{self.suffix}"


class TestApplyToColumnGroups(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame(
            [
                [1.0, None, 2.0],
                [None, 3.0, 4.0],
            ],
            columns=[_Ticker("asset_a", "1"), _Ticker("asset_a", "2"), _Ticker("asset_b", "1")],
        )

    def test_groups_columns_without_axis_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            grouped = apply_to_column_groups(
                self.frame,
                by=lambda ticker: ticker.name,
                func=lambda frame: frame.notna().any(axis=1),
            )

        self.assertEqual(["asset_a", "asset_b"], list(grouped.columns))
        self.assertEqual([True, True], grouped["asset_a"].tolist())
        self.assertEqual([True, True], grouped["asset_b"].tolist())
        self.assertFalse(any("groupby with axis=1 is deprecated" in str(w.message) for w in caught))

    def test_preserves_row_index_for_numeric_aggregation(self):
        grouped = apply_to_column_groups(
            self.frame,
            by=lambda ticker: ticker.name,
            func=lambda frame: frame.abs().max(axis=1),
        )

        self.assertEqual([0, 1], list(grouped.index))
        self.assertEqual([1.0, 3.0], grouped["asset_a"].tolist())
        self.assertEqual([2.0, 4.0], grouped["asset_b"].tolist())


if __name__ == "__main__":
    unittest.main()
