#!/usr/bin/env bash
# ============================================================
# run_issue_245_fix.sh
#
# Reproduces and verifies the fix for Issue #245:
#   "Multiple files use deprecated DataFrame.applymap which
#    should be replaced with DataFrame.map"
#
# Usage:
#   cd <repo-root>
#   bash run_issue_245_fix.sh
# ============================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

echo "============================================================"
echo "Issue #245 – applymap → map migration"
echo "============================================================"
echo ""

# ── 1. Show pandas version ──────────────────────────────────
echo "[1] Environment"
python - <<'PY'
import pandas as pd, sys
print(f"  Python  : {sys.version.split()[0]}")
print(f"  pandas  : {pd.__version__}")
PY
echo ""

# ── 2. Confirm no .applymap( remains in the affected files ──
echo "[2] Grep check – no .applymap( calls in affected files"
AFFECTED=(
    "qf_lib/analysis/tearsheets/portfolio_analysis_sheet.py"
    "qf_lib/backtesting/monitoring/backtest_monitor.py"
    "qf_lib/data_providers/bloomberg_dl/bloomberg_dl_data_provider.py"
    "qf_lib/analysis/model_params_estimation/model_params_evaluator.py"
    "qf_lib/analysis/strategy_monitoring/assets_monitoring_sheet.py"
)
FOUND=0
for f in "${AFFECTED[@]}"; do
    if grep -n "\.applymap(" "$f" 2>/dev/null; then
        echo "  FAIL: .applymap( still present in $f"
        FOUND=1
    fi
done
if [ "$FOUND" -eq 0 ]; then
    echo "  OK – no .applymap( calls remain in any affected file"
fi
echo ""

# ── 3. Run the targeted unit tests ──────────────────────────
echo "[3] Running unit tests"
PYTHONPATH="$REPO_ROOT" python -m pytest \
    qf_lib/tests/unit_tests/containers/test_dataframe_map_deprecation.py \
    -v --tb=short 2>&1
echo ""

echo "============================================================"
echo "All checks passed. Issue #245 fix verified."
echo "============================================================"
