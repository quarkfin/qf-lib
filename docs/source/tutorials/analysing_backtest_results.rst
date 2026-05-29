########################################
Analysing Backtest Results
########################################

After running a backtest, QF-Lib generates a rich set of output files and in-memory objects that let you
understand exactly how your strategy performed. This tutorial covers:

* What output files are produced and what each contains.
* How to compute key performance metrics from any price series using :class:`~qf_lib.analysis.timeseries_analysis.timeseries_analysis.TimeseriesAnalysis`.
* How to generate the different tearsheet documents - with benchmark, without benchmark, and comparative.
* How to analyse individual trades through :class:`~qf_lib.analysis.trade_analysis.trade_analysis_sheet.TradeAnalysisSheet`.

.. note::
    All code samples on this page are based on the demo data provider and can be run directly from the
    ``demo_scripts/common/`` folder of the repository.


*******************************************************
Understanding the output directory
*******************************************************

When you run a backtest with :class:`~qf_lib.backtesting.trading_session.backtest_trading_session_builder.BacktestTradingSessionBuilder`,
every result is written to a directory under ``output/backtesting/<backtest_name>/``.
The location of the ``output`` root is set by the ``output_directory`` key in your ``Settings`` JSON file.

The default output contains the following files:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Contents
   * - ``Transactions.csv``
     - One row per fill: timestamp, name  of the asset, contract symbol (ticker), security type (stock, future etc), contract size (important for e.g. futures), quantity, price and commission.
   * - ``Config.yaml``
     - A record of every parameter set on the :class:`~qf_lib.backtesting.trading_session.backtest_trading_session_builder.BacktestTradingSessionBuilder`
       (frequency, commission model, slippage model, position sizer, etc.).
   * - ``Timeseries.xlsx``
     - Daily end-of-day portfolio value time series (and optional leverage sheet).
   * - ``Portfolio Analysis Sheet.pdf``
     - Charts showing asset-level performance, position count, and exposure over time.
   * - ``Tearsheet.pdf``
     - Summary with performance metrics and the equity curve.
   * - ``Trades Analysis Sheet.pdf``
     - Trade-level statistics: win rate, average trade duration, best/worst trade return, etc.

These files are generated automatically by :class:`~qf_lib.backtesting.monitoring.backtest_monitor.BacktestMonitor`.
If you want to suppress output during a fast parameter sweep, pass
``BacktestMonitorSettings.no_stats()`` to ``session_builder.set_monitor_settings()``.

*******************************************************
Performance metrics reference
*******************************************************

The tearsheet and console output both print a standard table of risk/return metrics. The table below explains each one:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Metric
     - Definition
   * - **Total Return**
     - Cumulative return over the full period: ``(final_value / initial_value) - 1``.
   * - **Annualised Return (CAGR)**
     - Compound Annual Growth Rate - the geometric mean annual return.
   * - **Annualised Volatility**
     - Standard deviation of daily returns scaled to annual frequency.
   * - **Annualised Upside / Downside Vol.**
     - Volatility calculated using only positive / negative daily returns respectively.
   * - **Sharpe Ratio**
     - Difference between the portfolio returns and the risk-free return, divided by the standard deviation of the portfolio returns.
   * - **Sortino Ratio**
     - Difference between the portfolio returns and the risk-free return, divided by the standard deviation of the negative portfolio returns.
   * - **Omega Ratio**
     - Probability-weighted ratio of gains to losses above a threshold return.
   * - **Calmar Ratio**
     - Ratio comparing average annual returns to maximum drawdown.
   * - **Gain to Pain Ratio**
     - Sum of all returns divided by the absolute sum of all negative returns.
   * - **5% CVaR**
     - Conditional Value-at-Risk (expected shortfall) at the 5% level - average return on the worst 5% of days.
   * - **Max Drawdown**
     - Largest peak-to-trough decline in portfolio value.
   * - **Avg Drawdown**
     - Mean of all individual drawdown depths.
   * - **Avg Drawdown Duration**
     - Mean number of days spent below a previous high-water mark.
   * - **Best / Worst Return**
     - Largest single-day gain and loss.
   * - **Avg Positive / Negative Return**
     - Mean return on days with gains / losses.
   * - **Skewness**
     - Third moment of the return distribution. Positive skew means a long right tail (rare large gains).

*******************************************************
TimeseriesAnalysis
*******************************************************

:class:`~qf_lib.analysis.timeseries_analysis.timeseries_analysis.TimeseriesAnalysis` is a standalone
utility that computes all metrics above from any :class:`~qf_lib.containers.series.prices_series.PricesSeries`
or :class:`~qf_lib.containers.series.returns_series.ReturnsSeries`. You do not need to run a backtest first.

Analysing a single series
===========================
.. code-block:: python

    from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider

    start_date = str_to_date('2016-01-01')
    end_date = str_to_date('2017-12-31')

    # Get a price series for ticker AAA
    prices = daily_data_provider.get_price(
        tickers=DummyTicker('AAA'),
        fields=PriceField.Close,
        start_date=start_date,
        end_date=end_date,
    )

    ta = TimeseriesAnalysis(prices, Frequency.DAILY)

    # Pretty-print the full metrics table to the console
    print(TimeseriesAnalysis.values_in_table(ta))


Output of the code snippet above:

.. code-block:: text

                                              AAA
    Start Date                         2016-01-04
    End Date                           2017-12-29
    Total Return                            13.53 %
    Annualised Return                        6.59 %
    Annualised Volatility                   10.65 %
    Annualised Upside Vol.                   6.59 %
    Annualised Downside Vol.                 7.13 %
    Sharpe Ratio                             0.60
    Omega Ratio                              1.11
    Calmar Ratio                             0.57
    Gain to Pain Ratio                       0.54
    Sortino Ratio                            0.92
    5% CVaR                                 -1.49 %
    Annualised 5% CVaR                     -21.23 %
    Max Drawdown                            11.47 %
    Avg Drawdown                             4.01 %
    Avg Drawdown Duration                   32.81 days
    Best Return                              2.76 %
    Worst Return                            -2.56 %
    Avg Positive Return                      0.52 %
    Avg Negative Return                     -0.51 %
    Skewness                                -0.14
    No. of daily samples                      520


Analysing multiple series at once
====================================
If you have prices for several tickers in a :class:`~qf_lib.containers.dataframe.qf_dataframe.QFDataFrame`,
pass it to ``table_for_df`` to get a side-by-side comparison table:

.. code-block:: python

    from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider

    start_date = str_to_date('2016-01-01')
    end_date = str_to_date('2017-12-31')

    tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC'), DummyTicker('DDD')]

    prices_df = daily_data_provider.get_price(
        tickers=tickers,
        fields=PriceField.Close,
        start_date=start_date,
        end_date=end_date,
    )
    prices_df.ffill(inplace=True)  # forward-fill any gaps

    print(TimeseriesAnalysis.table_for_df(prices_df))

The result is a DataFrame with one row per metric and one column per ticker - convenient for programmatic
comparison.Output of the code snippet above:

.. code-block:: text

    Analysed period: 2016-01-04 - 2017-12-29, using daily data
    Name            total_ret        cagr         vol      up_vol    down_vol      sharpe       omega      calmar   gain/pain     sortino        cvar     cvar_an      max_dd      avg_dd  avg_dd_dur    best_ret   worst_ret avg_pos_ret avg_neg_ret    skewness     #observ
    AAA                 13.53        6.59       10.65        6.59        7.13        0.60        1.11        0.57        0.54        0.92       -1.49      -21.23       11.47        4.01       32.81        2.76       -2.56        0.52       -0.51       -0.14         520
    BBB                 36.32       16.87        9.96        6.85        5.44        1.56        1.29        1.40        1.86        3.10       -1.17      -17.01       12.04        3.29       24.36        2.24       -1.72        0.51       -0.47        0.31         520
    CCC                -35.35      -19.70       12.55        7.86        8.15       -1.75        0.77       -0.47       -0.73       -2.42       -1.80      -25.03       41.95       26.53      180.50        4.07       -2.82        0.58       -0.64        0.13         520
    DDD                 34.16       15.93       10.30        7.15        6.13        1.44        1.27        2.02        1.44        2.60       -1.25      -18.09        7.90        2.63       23.10        2.52       -2.65        0.52       -0.47        0.25         520


Accessing individual metrics
==============================
You can also read individual attributes from a :class:`~qf_lib.analysis.timeseries_analysis.timeseries_analysis.TimeseriesAnalysis`
object directly:

.. code-block:: python

    ta = TimeseriesAnalysis(prices, Frequency.DAILY)

    print("Sharpe:       ", ta.sharpe_ratio)
    print("Max Drawdown: ", ta.max_drawdown)
    print("CAGR:         ", ta.cagr)
    print("Sortino:      ", ta.sortino_ratio)


*******************************************************
Generating tearsheets
*******************************************************

Tearsheets can be generated independently of a backtest, from any two price series (strategy and benchmark).
There are three types:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Class
     - When to use
   * - :class:`~qf_lib.analysis.tearsheets.tearsheet_without_benchmark.TearsheetWithoutBenchmark`
     - You only have a strategy series and no benchmark to compare against.
   * - :class:`~qf_lib.analysis.tearsheets.tearsheet_with_benchmark.TearsheetWithBenchmark`
     - You want to show the strategy alongside a benchmark with relative performance charts.
   * - :class:`~qf_lib.analysis.tearsheets.tearsheet_comparative.TearsheetComparative`
     - You want to compare two strategies or a strategy vs benchmark side by side.

All three classes follow the same pattern: instantiate, call ``build_document()``, then ``save()``.

Tearsheet without benchmark
============================
.. code-block:: python

    from qf_lib.analysis.tearsheets.tearsheet_without_benchmark import TearsheetWithoutBenchmark
    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date
    from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
    from demo_scripts.demo_configuration.demo_settings import get_demo_settings

    start_date = str_to_date('2013-01-01')
    end_date = str_to_date('2017-12-31')

    strategy = daily_data_provider.get_price(
        tickers=DummyTicker('AAA'),
        fields=PriceField.Close,
        start_date=start_date,
        end_date=end_date,
    )
    strategy.name = "My Strategy"

    settings = get_demo_settings()
    pdf_exporter = PDFExporter(settings)

    tearsheet = TearsheetWithoutBenchmark(
        settings, pdf_exporter, strategy, title="Strategy Tearsheet"
    )
    tearsheet.build_document()
    tearsheet.save(file_name="Strategy Tearsheet")

Tearsheet with benchmark
==========================
Add a ``benchmark`` series and an optional ``live_date`` to mark the boundary between in-sample
and out-of-sample periods:

.. code-block:: python

    from qf_lib.analysis.tearsheets.tearsheet_with_benchmark import TearsheetWithBenchmark

    live_date = str_to_date('2015-01-01')  # strategy went live on this date

    benchmark = daily_data_provider.get_price(
        tickers=DummyTicker('BBB'),
        fields=PriceField.Close,
        start_date=start_date,
        end_date=end_date,
    )
    benchmark.name = "Benchmark"

    tearsheet = TearsheetWithBenchmark(
        settings, pdf_exporter, strategy, benchmark,
        live_date=live_date,
        title="Strategy vs Benchmark",
    )
    tearsheet.build_document()
    tearsheet.save(file_name="Strategy vs Benchmark")

The tearsheet will draw a vertical line at ``live_date`` to separate the backtested period from live trading.
If you omit ``live_date`` (or pass ``None``), no line is drawn.

Comparative tearsheet
======================
Use :class:`~qf_lib.analysis.tearsheets.tearsheet_comparative.TearsheetComparative` to overlay
two equity curves on the same page:

.. code-block:: python

    from qf_lib.analysis.tearsheets.tearsheet_comparative import TearsheetComparative

    tearsheet = TearsheetComparative(
        settings, pdf_exporter, strategy, benchmark,
        title="Strategy vs Benchmark Comparative",
    )
    tearsheet.build_document()
    tearsheet.save(file_name="Comparative Tearsheet")

*******************************************************
Trade analysis
*******************************************************

A **transaction** is a single fill (one buy or sell execution). A **trade** is a completed round-trip in one
asset: all fills from opening a position until it is flat again.

:class:`~qf_lib.backtesting.portfolio.backtest_position.BacktestPosition` stores that round-trip inside the
backtester. Each closed position records:

* ``start_time`` / ``end_time`` — when the position was opened and fully closed
* ``total_pnl`` and ``total_commission()`` — currency P&L including fees
* ``direction()`` — ``1`` for long, ``-1`` for short
* ``ticker()`` — the instrument

:class:`~qf_lib.analysis.trade_analysis.trades_generator.TradesGenerator` can build
:class:`~qf_lib.backtesting.portfolio.trade.Trade` objects in two equivalent ways:

1. **From closed positions** — ``portfolio.closed_positions()`` after a backtest (one trade per closed position).
2. **From transactions** — any sequence of :class:`~qf_lib.backtesting.portfolio.transaction.Transaction`
   objects, including rows loaded from ``Transactions.csv``.

Both paths use the same trade logic; unit tests verify that ``create_trades_from_transactions`` matches
``create_trades_from_backtest_positions`` for the same fills.


From closed ``BacktestPosition`` objects (in memory)
====================================================

After ``ts.start_trading()``, use closed positions and the portfolio NAV series so each trade gets a
**percentage P&L** (P&L divided by portfolio value at position open):

.. code-block:: python

    from qf_lib.analysis.trade_analysis.trade_analysis_sheet import TradeAnalysisSheet
    from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator

    trades_generator = TradesGenerator()
    closed_positions = ts.portfolio.closed_positions()
    portfolio_tms = ts.portfolio.portfolio_eod_series()

    trades = trades_generator.create_trades_from_backtest_positions(
        closed_positions, portfolio_tms
    )

    if trades:
        nr_of_assets = len({t.ticker.name for t in trades})
        start = portfolio_tms.index[0]
        end = portfolio_tms.index[-1]

        sheet = TradeAnalysisSheet(
            settings, pdf_exporter,
            nr_of_assets_traded=nr_of_assets,
            trades=trades,
            start_date=start,
            end_date=end,
            title="Trade Analysis",
        )
        sheet.build_document()
        sheet.save("output/backtesting/my_run")

:class:`~qf_lib.analysis.trade_analysis.trade_analysis_sheet.TradeAnalysisSheet` produces a PDF with win rate,
average trade duration, best/worst trade, return distributions, and related statistics.


From ``Transactions.csv`` (after the backtest)
==============================================

:class:`~qf_lib.backtesting.monitoring.backtest_monitor.BacktestMonitor` writes
``Transactions.csv`` when ``issue_transaction_log`` is enabled (default in
:class:`~qf_lib.backtesting.monitoring.backtest_monitor.BacktestMonitorSettings`).
Columns: ``Timestamp``, ``Asset Name``, ``Contract symbol``, ``Security type``, ``Contract size``,
``Quantity``, ``Price``, ``Commission``.

Use this when you want to rebuild trade analysis **without re-running** the backtest — for example from
an archived output folder.

.. code-block:: python

    import os

    import pandas as pd

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_settings import get_demo_settings
    from qf_lib.analysis.trade_analysis.trade_analysis_sheet import TradeAnalysisSheet
    from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
    from qf_lib.backtesting.portfolio.transaction import Transaction
    from qf_lib.containers.series.qf_series import QFSeries
    from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter

    def load_transactions_csv(path: str):
        """Map monitor CSV rows to Transaction objects (demo: DummyTicker per contract symbol)."""
        df = pd.read_csv(path)
        transactions = []
        for _, row in df.iterrows():
            # For Bloomberg or other providers, replace DummyTicker with your Ticker subclass.
            ticker = DummyTicker(row["Contract symbol"])
            transactions.append(Transaction(
                pd.to_datetime(row["Timestamp"]),
                ticker,
                row["Quantity"],
                row["Price"],
                row["Commission"],
            ))
        return transactions

    def load_portfolio_eod_xlsx(path: str) -> QFSeries:
        """Load NAV from Timeseries.xlsx written by BacktestMonitor (first data column)."""
        df = pd.read_excel(path, index_col=0, parse_dates=True)
        series = QFSeries(df.iloc[:, 0])
        series.name = "Portfolio"
        return series

    def main():
        # Folder produced by BacktestMonitor, e.g. output/backtesting/<backtest_name>/
        report_dir = "output/backtesting/my_backtest"
        transactions_path = os.path.join(report_dir, "2025_01_15-1200 Transactions.csv")
        timeseries_path = os.path.join(report_dir, "2025_01_15-1200 Timeseries.xlsx")

        settings = get_demo_settings()
        pdf_exporter = PDFExporter(settings)

        transactions = load_transactions_csv(transactions_path)
        portfolio_tms = load_portfolio_eod_xlsx(timeseries_path)

        trades_generator = TradesGenerator()
        trades = trades_generator.create_trades_from_transactions(transactions, portfolio_tms)

        if not trades:
            print("No closed round-trip trades found in the CSV.")
            return

        nr_of_assets = len({t.ticker.name for t in trades})
        start_date = min(t.start_time for t in trades)
        end_date = max(t.end_time for t in trades)

        sheet = TradeAnalysisSheet(
            settings, pdf_exporter,
            nr_of_assets_traded=nr_of_assets,
            trades=trades,
            start_date=start_date,
            end_date=end_date,
            title="Trade Analysis from CSV",
        )
        sheet.build_document()
        sheet.save(report_dir)

    if __name__ == "__main__":
        main()

.. note::
    * Match the actual filenames in your output folder (timestamp prefix varies per run).
    * ``load_transactions_csv`` must construct the same :class:`~qf_lib.common.tickers.tickers.Ticker`
      types you used in the backtest. The demo uses ``DummyTicker`` from ``demo_scripts``; for live data use
      e.g. :class:`~qf_lib.common.tickers.tickers.BloombergTicker` and map
      ``Security type`` / ``Contract size`` from the CSV.
    * If you omit ``portfolio_tms``, trades are still created but ``percentage_pnl`` may be empty and some
      charts in the sheet will be limited.


Reading trade results programmatically
=======================================
Each :class:`~qf_lib.backtesting.portfolio.trade.Trade` exposes:

.. code-block:: python

    for trade in trades:
        print(f"Ticker:   {trade.ticker}")
        print(f"P&L:      {trade.pnl:.2f}")
        if trade.percentage_pnl is not None:
            print(f"P&L (%):  {trade.percentage_pnl:.2%}")
        print(f"Direction: {trade.direction}")
        print(f"Open:     {trade.start_time}  →  Close: {trade.end_time}")

Example output:

.. code-block:: text

    Ticker:   DummyTicker('AAA')
    P&L:      399319.04
    P&L (%):  4.01%
    Direction: 1.0
    Open:     2010-01-01 13:30:00  →  Close: 2010-02-09 13:30:00

    Ticker:   DummyTicker('AAA')
    P&L:      -35780.43
    P&L (%):  -0.34%
    Direction: 1.0
    Open:     2010-03-25 13:30:00  →  Close: 2010-04-09 13:30:00

