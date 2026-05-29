########################################
Fast Alpha Model Testing
########################################

Running a full backtest for every combination of strategy parameters is slow. QF-Lib provides a
Monte Carlo-based shortcut that:

1. Runs one or more *lightweight* backtests to collect trade return distributions.
2. Uses :class:`~qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator.ScenariosGenerator`
   to bootstrap thousands of synthetic equity curves from those distributions.
3. Uses :class:`~qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats.InitialRiskStatsFactory`
   to score each parameter combination against acceptance criteria (target return and max drawdown).

This is useful for:

* Sweeping the ``initial_risk`` parameter of
  :class:`~qf_lib.backtesting.position_sizer.initial_risk_position_sizer.InitialRiskPositionSizer`.
* Sweeping hyperparameters of an ``AlphaModel`` (e.g. fast/slow MA periods).
* Quickly identifying parameter regions that are likely to fail before committing to full backtests.

All code in this tutorial is based on
``demo_scripts/backtester/compare_different_initial_risks.py``.



*******************************************************
Key concepts
*******************************************************

Trade return distribution
==========================
A *trade* is a round-trip: an open followed by a close. After a backtest the percentage P&L of each
trade is stored in ``trade.percentage_pnl``. The fast tester uses this distribution as the atom of the
Monte Carlo simulation - it treats trades as exchangeable and bootstraps sequences of them.

Scenarios
==========
A *scenario* is a synthetic sequence of ``scenarios_length`` trade returns drawn with replacement from
the empirical distribution. With ``num_of_scenarios`` such sequences the
:class:`~qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator.ScenariosGenerator` produces a
DataFrame of shape ``(num_of_scenarios, scenarios_length)`` - one row per simulated "life" of the strategy.

Acceptance statistics
======================
:class:`~qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats.InitialRiskStatsFactory`
applies two criteria to each set of scenarios:

* **target_return** - the fraction of scenarios that achieve at least this cumulative return.
* **max_accepted_dd** - the fraction of scenarios whose maximum drawdown stays below this level.

It returns a summary DataFrame that you can inspect to decide which parameter values are acceptable.


*******************************************************
Step 1 - Collect trade returns from a backtest
*******************************************************

The helper function below runs a single backtest and extracts trade percentage P&L values:

.. code-block:: python

    from typing import List

    from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
    from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
    from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
        CalculateAndPlaceOrdersRegularEvent
    from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitorSettings
    from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
    from qf_lib.backtesting.strategies.alpha_model_strategy import AlphaModelStrategy
    from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
    from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date
    from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
    from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter

    from demo_scripts.backtester.moving_average_alpha_model import MovingAverageAlphaModel
    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
    from demo_scripts.demo_configuration.demo_settings import get_demo_settings


    def run_backtest(init_risk: float) -> BacktestTradingSession:
        """Build and run a backtest with the given initial_risk value."""
        start_date = str_to_date('2016-01-01')
        end_date = str_to_date('2017-12-31')

        settings = get_demo_settings()
        pdf_exporter = PDFExporter(settings)
        excel_exporter = ExcelExporter(settings)

        session_builder = BacktestTradingSessionBuilder(settings, pdf_exporter, excel_exporter)
        session_builder.set_data_provider(daily_data_provider)
        session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk=init_risk)
        session_builder.set_frequency(Frequency.DAILY)
        # Suppress per-backtest output files during the sweep
        session_builder.set_monitor_settings(BacktestMonitorSettings.no_stats())
        session_builder.set_backtest_name(f"Initial Risk {init_risk}")

        ts = session_builder.build(start_date, end_date)
        return ts


    def get_trade_returns(ts: BacktestTradingSession, model: AlphaModel) -> List[float]:
        """Run the strategy on an already-built session and return trade P&L values."""
        model_tickers_dict = {model: [DummyTicker('BBB')]}

        strategy = AlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=True)
        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

        trades_generator = TradesGenerator()
        positions = ts.portfolio.closed_positions()
        portfolio_tms = ts.portfolio.portfolio_eod_series()
        trades = trades_generator.create_trades_from_backtest_positions(positions, portfolio_tms)

        return [t.percentage_pnl for t in trades]


*******************************************************
Step 2 - Generate Monte Carlo scenarios
*******************************************************

:class:`~qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator.ScenariosGenerator` bootstraps
the trade return list into a large matrix of synthetic equity curves:

.. code-block:: python

    from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator

    scenarios_generator = ScenariosGenerator()

    # Example: 500 scenarios of 120 trades each
    trade_returns = get_trade_returns(ts, model)   # obtained from step 1
    scenarios_df = scenarios_generator.make_scenarios(
        trade_returns,
        scenarios_length=120,   # how many trades per synthetic run
        num_of_scenarios=1000,  # how many parallel runs
    )

    print(f"Scenarios matrix shape: {scenarios_df.shape}")
    # Each row is a scenario; each column is a cumulative equity value after N trades.


*******************************************************
Step 3 - Score parameters against acceptance criteria
*******************************************************

:class:`~qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats.InitialRiskStatsFactory`
takes a list of parameter values and the corresponding list of scenario DataFrames, and computes the
fraction of scenarios that pass both the return and drawdown criteria:

.. code-block:: python

    from qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats import InitialRiskStatsFactory

    stats_factory = InitialRiskStatsFactory(
        max_accepted_dd=0.30,   # reject scenarios with max drawdown > 30%
        target_return=0.10,     # target 10% cumulative return over the scenario
    )

    # ... (populate scenarios_df_list in the loop below) ...
    stats = stats_factory.make_stats(initial_risks_list, scenarios_df_list)
    print(stats)


*******************************************************
Full example - sweeping initial risk
*******************************************************

Putting it all together: we test five different ``initial_risk`` values and print acceptance statistics
for each:

.. code-block:: python

    from time import time

    initial_risks_list = [0.001, 0.005, 0.01, 0.02, 0.05]
    scenarios_df_list = []

    stats_factory = InitialRiskStatsFactory(max_accepted_dd=0.30, target_return=0.10)
    scenarios_generator = ScenariosGenerator()

    print(f"Testing {len(initial_risks_list)} parameter sets...")

    for i, init_risk in enumerate(initial_risks_list, 1):
        t0 = time()

        ts = run_backtest(init_risk)
        model = MovingAverageAlphaModel(10, 30, 2, ts.data_provider)
        rets = get_trade_returns(ts, model)

        scenarios_df = scenarios_generator.make_scenarios(
            rets, scenarios_length=100, num_of_scenarios=1000
        )
        scenarios_df_list.append(scenarios_df)

        print(f"  [{i}/{len(initial_risks_list)}]  init_risk={init_risk}  "
              f"trades={len(rets)}  time={time()-t0:.1f}s")

    stats = stats_factory.make_stats(initial_risks_list, scenarios_df_list)
    print("\n=== Acceptance statistics ===")
    print(stats)

The output is a summary table with one row per ``initial_risk`` value showing:

* The fraction of scenarios that reached the target return.
* The fraction of scenarios that stayed within the max drawdown limit.
* A combined acceptance score.


*******************************************************
Sweeping alpha model hyperparameters
*******************************************************

The same pattern works for any set of hyperparameters. Here we sweep the ``fast_time_period`` of a
:class:`~qf_lib.backtesting.alpha_model.alpha_model.AlphaModel`:

.. code-block:: python

    from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitorSettings

    fast_periods = [3, 5, 10, 15, 20]
    slow_period = 30
    init_risk = 0.02

    scenarios_df_list = []
    fast_period_labels = []

    for fast in fast_periods:
        ts = run_backtest(init_risk)
        model = MovingAverageAlphaModel(
            fast_time_period=fast,
            slow_time_period=slow_period,
            risk_estimation_factor=1.25,
            data_provider=ts.data_provider,
        )
        rets = get_trade_returns(ts, model)

        scenarios_df = scenarios_generator.make_scenarios(
            rets, scenarios_length=100, num_of_scenarios=1000
        )
        scenarios_df_list.append(scenarios_df)
        fast_period_labels.append(fast)
        print(f"fast={fast}  trades={len(rets)}")

    stats = stats_factory.make_stats(fast_period_labels, scenarios_df_list)
    print(stats)

.. tip::
    Disable monitoring output (``BacktestMonitorSettings.no_stats()``) in parameter sweeps -
    it avoids writing hundreds of files and speeds up each iteration significantly.




