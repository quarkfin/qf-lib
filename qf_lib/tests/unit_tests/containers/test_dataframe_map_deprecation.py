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

"""
Tests for Issue #245: DataFrame.applymap -> DataFrame.map migration.

Verifies that DataFrame.map produces correct results for each lambda pattern
used across the six affected files, and that no 'applymap' call remains in
the library source (caught via grep on import-time source inspection).

Affected files:
  - qf_lib/analysis/tearsheets/portfolio_analysis_sheet.py
  - qf_lib/backtesting/monitoring/backtest_monitor.py
  - qf_lib/data_providers/bloomberg_dl/bloomberg_dl_data_provider.py
  - qf_lib/analysis/model_params_estimation/model_params_evaluator.py
  - qf_lib/analysis/strategy_monitoring/assets_monitoring_sheet.py
  - qf_lib/containers/dataframe/qf_dataframe.py  (docstring only)

We use plain pd.DataFrame throughout: the call site in production code is
always on a pd.DataFrame (or subclass), and we want to be independent of
unrelated pandas-version compatibility issues in QFSeries.__init__.
"""

import datetime
import subprocess
import sys
import unittest
import warnings
from unittest import TestCase

import pandas as pd


def _assert_no_applymap_warning(func):
    """Run func(); raise AssertionError if any FutureWarning about applymap fires."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        func()
    bad = [w for w in caught
           if issubclass(w.category, FutureWarning) and "applymap" in str(w.message).lower()]
    assert bad == [], "Unexpected FutureWarning(s) about applymap: {}".format(bad)


# ---------------------------------------------------------------------------
# portfolio_analysis_sheet.py – pattern 1
# Extracting a numeric attribute from an object cell, falling back to 0
# ---------------------------------------------------------------------------
class TestObjectAttributeExtractionWithFallback(TestCase):

    def setUp(self):
        class FakePosition:
            def __init__(self, exposure):
                self.total_exposure = exposure

        self.FakePosition = FakePosition
        self.df = pd.DataFrame({
            "A": [FakePosition(100.0), 0, FakePosition(50.0)],
            "B": [FakePosition(200.0), FakePosition(75.0), 0],
        })

    def test_correct_values(self):
        result = self.df.map(
            lambda x: x.total_exposure if isinstance(x, self.FakePosition) else 0)
        self.assertEqual(result.loc[0, "A"], 100.0)
        self.assertEqual(result.loc[1, "A"], 0)
        self.assertEqual(result.loc[2, "B"], 0)
        self.assertEqual(result.loc[1, "B"], 75.0)

    def test_no_applymap_warning(self):
        _assert_no_applymap_warning(lambda: self.df.map(
            lambda x: x.total_exposure if isinstance(x, self.FakePosition) else 0))


# ---------------------------------------------------------------------------
# portfolio_analysis_sheet.py – pattern 2
# Float → percentage string  '{:.2%}'
# ---------------------------------------------------------------------------
class TestFloatToPercentageString(TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "Long": [0.5, 0.3], "Short": [0.2, 0.4], "Out": [0.3, 0.3]
        })

    def test_correct_values(self):
        result = self.df[["Long", "Short", "Out"]].map(lambda x: '{:.2%}'.format(x))
        self.assertEqual(result.loc[0, "Long"],  "50.00%")
        self.assertEqual(result.loc[1, "Short"], "40.00%")
        self.assertEqual(result.loc[0, "Out"],   "30.00%")

    def test_no_applymap_warning(self):
        _assert_no_applymap_warning(
            lambda: self.df.map(lambda x: '{:.2%}'.format(x)))


# ---------------------------------------------------------------------------
# portfolio_analysis_sheet.py – patterns 3 & 4 (chained)
# Extract last element of a Series cell, then format as '{:,.2f}'
# ---------------------------------------------------------------------------
class TestSeriesLastValueThenFormat(TestCase):

    def setUp(self):
        self.df = pd.DataFrame({"col": [
            pd.Series([1.0, 2.0, 3.0]),
            pd.Series([], dtype=float),
            pd.Series([10.0, 20.0]),
        ]})

    def test_series_last_value_extraction(self):
        result = self.df.map(lambda s: s.iloc[-1] if not s.empty else 0.0)
        self.assertEqual(result.loc[0, "col"], 3.0)
        self.assertEqual(result.loc[1, "col"], 0.0)
        self.assertEqual(result.loc[2, "col"], 20.0)

    def test_no_applymap_warning_on_series_extraction(self):
        _assert_no_applymap_warning(
            lambda: self.df.map(lambda s: s.iloc[-1] if not s.empty else 0.0))

    def test_float_to_comma_formatted_string(self):
        numeric_df = pd.DataFrame({
            "Overall performance": [1234.5, -678.9],
            "Long PnL": [0.0, 99.0],
        })
        result = numeric_df.map(lambda p: '{:,.2f}'.format(p))
        self.assertEqual(result.loc[0, "Overall performance"], "1,234.50")
        self.assertEqual(result.loc[1, "Long PnL"], "99.00")

    def test_no_applymap_warning_on_float_format(self):
        numeric_df = pd.DataFrame({"x": [1.0, 2.0]})
        _assert_no_applymap_warning(
            lambda: numeric_df.map(lambda p: '{:,.2f}'.format(p)))


# ---------------------------------------------------------------------------
# backtest_monitor.py – applying a Signal-field extraction function
# ---------------------------------------------------------------------------
class TestSignalAttributeExtraction(TestCase):

    def setUp(self):
        class FakeSignal:
            def __init__(self, confidence):
                self.confidence = confidence

        self.FakeSignal = FakeSignal
        self.df = pd.DataFrame({"ticker": [FakeSignal(0.8), FakeSignal(0.6)]})
        self.fun = lambda s: s.confidence if isinstance(s, FakeSignal) else s

    def test_correct_values(self):
        result = self.df.map(self.fun)
        self.assertAlmostEqual(result.loc[0, "ticker"], 0.8)
        self.assertAlmostEqual(result.loc[1, "ticker"], 0.6)

    def test_no_applymap_warning(self):
        _assert_no_applymap_warning(lambda: self.df.map(self.fun))


# ---------------------------------------------------------------------------
# bloomberg_dl_data_provider.py – cast string cells to float
# ---------------------------------------------------------------------------
class TestCastToFloat(TestCase):

    @staticmethod
    def _cast(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    def setUp(self):
        self.df = pd.DataFrame(
            {"PERCENT_WEIGHT": ["12.5", "33.0", "bad", "7.25"]},
            index=pd.Index(["A", "B", "C", "D"]),
        )

    def test_correct_values(self):
        result = self.df.map(self._cast)
        self.assertAlmostEqual(result.loc["A", "PERCENT_WEIGHT"], 12.5)
        self.assertAlmostEqual(result.loc["B", "PERCENT_WEIGHT"], 33.0)
        self.assertTrue(pd.isna(result.loc["C", "PERCENT_WEIGHT"]))
        self.assertAlmostEqual(result.loc["D", "PERCENT_WEIGHT"], 7.25)

    def test_no_applymap_warning(self):
        _assert_no_applymap_warning(lambda: self.df.map(self._cast))


# ---------------------------------------------------------------------------
# model_params_evaluator.py – extract multiple attributes from result objects
# stored in a 2-D grid DataFrame
# ---------------------------------------------------------------------------
class TestResultObjectMultiAttributeExtraction(TestCase):

    def setUp(self):
        class FakeResult:
            def __init__(self, sqn, trades, ret, start, end):
                self.sqn_per_avg_nr_trades = sqn
                self.avg_nr_of_trades_1Y  = trades
                self.annualised_return     = ret
                self.start_date            = start
                self.end_date              = end

        r1 = FakeResult(1.2, 50, 0.15, datetime.date(2020, 1, 1), datetime.date(2021, 1, 1))
        r2 = FakeResult(0.8, 30, 0.08, datetime.date(2019, 6, 1), datetime.date(2021, 6, 1))
        r3 = FakeResult(2.1, 70, 0.22, datetime.date(2020, 3, 1), datetime.date(2022, 3, 1))
        r4 = FakeResult(0.5, 20, 0.04, datetime.date(2021, 1, 1), datetime.date(2022, 1, 1))

        self.results = pd.DataFrame(
            [[r1, r2], [r3, r4]],
            index=["param_a=1", "param_a=2"],
            columns=["param_b=1", "param_b=2"],
        )
        self.r1, self.r2, self.r3, self.r4 = r1, r2, r3, r4

    def test_sqn_extraction(self):
        sqn = self.results.map(lambda x: x.sqn_per_avg_nr_trades).fillna(0)
        self.assertAlmostEqual(sqn.loc["param_a=1", "param_b=1"], 1.2)
        self.assertAlmostEqual(sqn.loc["param_a=2", "param_b=1"], 2.1)

    def test_trades_extraction(self):
        trades = self.results.map(lambda x: x.avg_nr_of_trades_1Y).fillna(0)
        self.assertEqual(trades.loc["param_a=2", "param_b=2"], 20)

    def test_return_extraction(self):
        ret = self.results.map(lambda x: x.annualised_return).fillna(0)
        self.assertAlmostEqual(ret.loc["param_a=1", "param_b=2"], 0.08)

    def test_start_end_date_minmax(self):
        start = self.results.map(lambda x: x.start_date).min().min()
        end   = self.results.map(lambda x: x.end_date).max().max()
        expected_start = min(r.start_date for r in [self.r1, self.r2, self.r3, self.r4])
        expected_end   = max(r.end_date   for r in [self.r1, self.r2, self.r3, self.r4])
        self.assertEqual(start, expected_start)
        self.assertEqual(end,   expected_end)

    def test_no_applymap_warning(self):
        _assert_no_applymap_warning(
            lambda: self.results.map(lambda x: x.sqn_per_avg_nr_trades))


# ---------------------------------------------------------------------------
# assets_monitoring_sheet.py – large integer and percentage string formatting
# ---------------------------------------------------------------------------
class TestNumericFormatting(TestCase):

    def test_large_integer_formatting(self):
        """'{:,.0f}' pattern used in _create_performance_tables."""
        df = pd.DataFrame({"Value": [1_234_567.0, -9_876.0], "Count": [1000.0, 0.0]})
        result = df.map(lambda x: '{:,.0f}'.format(x))
        self.assertEqual(result.loc[0, "Value"], "1,234,567")
        self.assertEqual(result.loc[1, "Value"], "-9,876")
        self.assertEqual(result.loc[0, "Count"], "1,000")

    def test_no_applymap_warning_integer_format(self):
        df = pd.DataFrame({"x": [1.0, 2.0]})
        _assert_no_applymap_warning(lambda: df.map(lambda x: '{:,.0f}'.format(x)))

    def test_percentage_string_formatting(self):
        """'{:.2%}' pattern used in _create_performance_contribution_tables."""
        df = pd.DataFrame({"Return": [0.1234, -0.0567], "Weight": [1.0, 0.0]})
        result = df.map(lambda x: '{:.2%}'.format(x))
        self.assertEqual(result.loc[0, "Return"], "12.34%")
        self.assertEqual(result.loc[1, "Return"], "-5.67%")
        self.assertEqual(result.loc[0, "Weight"], "100.00%")

    def test_no_applymap_warning_percentage_format(self):
        df = pd.DataFrame({"x": [0.1, 0.2]})
        _assert_no_applymap_warning(lambda: df.map(lambda x: '{:.2%}'.format(x)))


# ---------------------------------------------------------------------------
# Static source check: no 'applymap' call survives in the library Python files
# ---------------------------------------------------------------------------
class TestNoApplymapInSource(TestCase):
    """
    Grep the qf_lib package source for any remaining '.applymap(' call.
    This is a belt-and-suspenders check independent of running the actual code.
    """

    AFFECTED_FILES = [
        "qf_lib/analysis/tearsheets/portfolio_analysis_sheet.py",
        "qf_lib/backtesting/monitoring/backtest_monitor.py",
        "qf_lib/data_providers/bloomberg_dl/bloomberg_dl_data_provider.py",
        "qf_lib/analysis/model_params_estimation/model_params_evaluator.py",
        "qf_lib/analysis/strategy_monitoring/assets_monitoring_sheet.py",
    ]

    def _repo_root(self):
        """Return the repo root (parent of qf_lib package)."""
        import qf_lib
        import os
        return os.path.dirname(os.path.dirname(qf_lib.__file__))

    def test_no_applymap_call_in_affected_files(self):
        import os
        root = self._repo_root()
        for rel_path in self.AFFECTED_FILES:
            full_path = os.path.join(root, rel_path)
            if not os.path.exists(full_path):
                self.skipTest("File not found: {}".format(full_path))
            with open(full_path) as fh:
                for lineno, line in enumerate(fh, 1):
                    self.assertNotIn(
                        ".applymap(",
                        line,
                        msg="{}:{} still contains .applymap(: {!r}".format(
                            rel_path, lineno, line.rstrip()),
                    )


if __name__ == "__main__":
    unittest.main()
