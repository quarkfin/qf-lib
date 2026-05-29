########################################
Glossary
########################################

This page defines the key terms used throughout the QF-Lib documentation.

.. glossary::
   :sorted:

   Ticker
      A typed identifier for a tradable instrument. QF-Lib uses different subclasses per data
      provider so the provider can interpret the symbol correctly (e.g.
      :class:`~qf_lib.common.tickers.tickers.BloombergTicker` for Bloomberg,
      :class:`~qf_lib.common.tickers.tickers.AlpacaTicker` for Alpaca).
      Use ``DummyTicker`` for demo and test data.

   SecurityType
      Enum that classifies an instrument: ``STOCK``, ``CRYPTO``, ``FUTURE``, etc.
      Used together with a :term:`Ticker` subclass to tell the data provider what kind of
      instrument is being requested.

   PriceField
      Enum selecting one column of bar data: ``Open``, ``High``, ``Low``, ``Close``, ``Volume``.
      See :doc:`tutorials/working_with_data`.

   Frequency
      Enum defining bar size: ``DAILY``, ``MIN_1``, ``MIN_5``, ``MIN_15``, ``MIN_30``, ``MIN_60``,
      ``WEEKLY``, ``MONTHLY``. Set on the session builder with
      ``session_builder.set_frequency(Frequency.DAILY)``.

   DataProvider
      The interface for fetching market data. Implementations include
      :class:`~qf_lib.data_providers.csv.csv_data_provider.CSVDataProvider`,
      :class:`~qf_lib.data_providers.bloomberg.bloomberg_data_provider.BloombergDataProvider`,
      :class:`~qf_lib.data_providers.alpaca_py.alpaca_data_provider.AlpacaDataProvider`, etc.
      All share the same ``get_price`` / ``historical_price`` interface. Inside a backtest, use
      ``ts.data_provider`` (or ``self.data_provider`` on a strategy); it respects the simulation clock
      so that requests at time ``t`` only see data up to and including ``t``.

   BacktestTradingSession
      The central object that wires together all components of a backtest: data provider, broker,
      portfolio, order factory, event manager, monitors, and exporters.
      Created by :class:`~qf_lib.backtesting.trading_session.backtest_trading_session_builder.BacktestTradingSessionBuilder`.

   BacktestTradingSessionBuilder
      The fluent builder used to configure and create a :term:`BacktestTradingSession`.
      Set frequency, data provider, commission model, slippage model, and position sizer before
      calling ``.build(start_date, end_date)``.

   Event
      The core primitive of the event-driven architecture. Every time step in the backtest
      corresponds to dispatching one or more events (e.g. ``MarketOpenEvent``,
      ``CalculateAndPlaceOrdersRegularEvent``, ``MarketCloseEvent``). Strategies subscribe to
      events and are called when those events fire. See :doc:`reference/backtest_flow`.

   Strategy
      Any class that extends :class:`~qf_lib.backtesting.strategies.abstract_strategy.AbstractStrategy`
      and implements ``calculate_and_place_orders()``. The method is called each time the subscribed
      event fires. See :doc:`tutorials/first_strategy_backtest`.

   AlphaModel
      An abstract signal generator that, given a :term:`Ticker` and its current
      :term:`Exposure`, returns a new desired :term:`Exposure`. Implement
      ``calculate_exposure(ticker, current_exposure) -> Exposure``.
      See :doc:`tutorials/first_alpha_model`.

   AlphaModelStrategy
      A pre-built :term:`Strategy` that drives one or more :term:`AlphaModel` objects.
      On each event it calls ``calculate_exposure()`` for every ticker, generates
      :term:`Signal` objects, and passes them to the :term:`PositionSizer`.

   Signal
      The output of an :term:`AlphaModel`. Contains:

      * ``suggested_exposure`` - the recommended :term:`Exposure` (``LONG``, ``SHORT``, or ``OUT``).
      * ``fraction_at_risk`` - the ATR-normalised distance from entry to stop-loss level.
      * ``confidence`` - optional scalar in [0, 1].
      * ``expected_move`` - optional scalar indicating the model's price target.

   Exposure
      Enum with three values used by :term:`AlphaModel` to express a directional view.
      The model returns only direction; :term:`PositionSizer` turns it into order size.

      * ``Exposure.LONG`` - buy / hold a long position (profit when price rises).
      * ``Exposure.SHORT`` - hold a short position (profit when price falls).
      * ``Exposure.OUT`` - no position (flat).

   PositionSizer
      Converts :term:`Signal` objects into sized :term:`Order` objects. Built-in options:

      * :class:`~qf_lib.backtesting.position_sizer.simple_position_sizer.SimplePositionSizer` -
        100% of portfolio per signal (default).
      * :class:`~qf_lib.backtesting.position_sizer.fixed_portfolio_percentage_position_sizer.FixedPortfolioPercentagePositionSizer` -
        allocates a fixed percentage of portfolio per signal.
      * :class:`~qf_lib.backtesting.position_sizer.initial_risk_position_sizer.InitialRiskPositionSizer` -
        sizes so that hitting the stop loss risks at most ``initial_risk`` of portfolio.
      * :class:`~qf_lib.backtesting.position_sizer.initial_risk_with_volume_position_sizer.InitialRiskWithVolumePositionSizer` -
        same as initial-risk sizing, capped by recent average volume.

   Order
      An instruction to buy or sell a quantity of a :term:`Ticker` with a given
      :class:`~qf_lib.backtesting.order.execution_style.ExecutionStyle`
      (``MarketOrder``, ``StopOrder``, ``MarketOnCloseOrder``) and
      :class:`~qf_lib.backtesting.order.time_in_force.TimeInForce` (``DAY``, ``GTC``).

   ExecutionStyle
      Specifies *how* an :term:`Order` is filled:

      * ``MarketOrder`` - fills at the next available price.
      * ``StopOrder`` - becomes a market order when price crosses the stop level.
      * ``MarketOnCloseOrder`` - fills at the market close price.

   Transaction
      A record of a single fill event: ticker, quantity filled, fill price and commission.
      Multiple transactions can belong to the same logical :term:`Trade`.

   Trade
      A round-trip: all :term:`Transaction` objects that open and then close one directional
      position in a given :term:`Ticker`. Computed post-backtest by
      :class:`~qf_lib.analysis.trade_analysis.trades_generator.TradesGenerator`.

   Position
      An open or closed holding of one asset in the portfolio. The
      :class:`~qf_lib.backtesting.portfolio.backtest_position.BacktestPosition` tracks quantity,
      average entry price, and unrealised P&L in real time during the backtest.
      :term:`Closed positions <Trade>` are collected via ``ts.portfolio.closed_positions()``.

   Portfolio
      Tracks the current holdings, cash balance, and total value in real time during a backtest.
      Accessible as ``ts.portfolio``. Key methods:

      * ``portfolio_eod_series()`` - time series of end-of-day portfolio value.
      * ``closed_positions()`` - list of all closed :term:`Position` objects.
      * ``open_positions_dict`` - dict of currently open positions keyed by ticker.

   CommissionModel
      Determines the commission charged per transaction. Built-in models:
      :class:`~qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model.FixedCommissionModel`,
      :class:`~qf_lib.backtesting.execution_handler.commission_models.bps_trade_value_commission_model.BpsTradeValueCommissionModel`,
      :class:`~qf_lib.backtesting.execution_handler.commission_models.ib_commission_model.IBCommissionModel`.
      See :doc:`tutorials/customize_your_backtest`.

   Slippage
      The difference between the expected fill price and the actual fill price, caused by
      market impact and bid-ask spread. Built-in models:
      :class:`~qf_lib.backtesting.execution_handler.slippage.fixed_slippage.FixedSlippage`,
      :class:`~qf_lib.backtesting.execution_handler.slippage.price_based_slippage.PriceBasedSlippage`,
      :class:`~qf_lib.backtesting.execution_handler.slippage.square_root_market_impact_slippage.SquareRootMarketImpactSlippage`.
      See :doc:`tutorials/customize_your_backtest`.

   OrdersFilter
      A pre-execution hook that adjusts or cancels orders before they reach the simulated broker.
      See :doc:`tutorials/how_to_guides`.

   OrderFactory
      A helper on the :term:`BacktestTradingSession` (``ts.order_factory``) that converts
      portfolio-relative targets into explicit :term:`Order` quantities. Key methods:

      * ``target_percent_orders(target_dict, execution_style, time_in_force)`` - generates orders
        to move each ticker's weight to the specified fraction of portfolio value.
      * ``orders(quantity_dict, execution_style, time_in_force)`` - generates orders for explicit
        quantities.

   Tearsheet
      A one-page PDF summary of a strategy's performance. Three variants:
      :class:`~qf_lib.analysis.tearsheets.tearsheet_without_benchmark.TearsheetWithoutBenchmark`,
      :class:`~qf_lib.analysis.tearsheets.tearsheet_with_benchmark.TearsheetWithBenchmark`,
      :class:`~qf_lib.analysis.tearsheets.tearsheet_comparative.TearsheetComparative`.
      See :doc:`tutorials/analysing_backtest_results`.

   TimeseriesAnalysis
      A utility that computes a full set of risk/return metrics (Sharpe, Sortino, CAGR,
      Max Drawdown, etc.) from any price or return series.
      See :doc:`tutorials/analysing_backtest_results`.

   QFSeries
      A typed subclass of :class:`pandas.Series` with a :class:`~pandas.DatetimeIndex`, used
      throughout QF-Lib for time-indexed scalar data (prices, returns, signals).

   QFDataFrame
      A typed subclass of :class:`pandas.DataFrame` with a :class:`~pandas.DatetimeIndex`.
      Used for multi-asset price or return data (rows = dates, columns = tickers or fields).

   QFDataArray
      A three-dimensional extension of the containers (ticker × date × field), backed by
      :class:`xarray.DataArray`. Returned when ``get_price`` is called with multiple tickers
      *and* multiple fields simultaneously.

   PricesSeries
      A :term:`QFSeries` that represents a series of prices. Provides ``.to_log_returns()``
      and ``.to_simple_returns()`` for converting to return series.

   ReturnsSeries
      A :term:`QFSeries` of returns (either simple or log). Provides ``.to_prices()`` to
      reconstruct a price series.

   ScenariosGenerator
      Bootstraps a trade return distribution into a matrix of Monte Carlo equity curves.
      Used in the :doc:`tutorials/fast_alpha_model_testing` workflow.

   InitialRiskStatsFactory
      Scores parameter combinations from Monte Carlo scenarios against a target return and
      maximum drawdown criterion. See :doc:`tutorials/fast_alpha_model_testing`.

