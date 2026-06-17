########################################
How-To Guides
########################################

This page contains short, focused recipes for common tasks in QF-Lib. Each section answers one specific
question with a minimal, runnable code example.



*******************************************************
How to use stop losses
*******************************************************

Stop losses automatically close a position when it moves against you by a configurable amount. They
are built into :class:`~qf_lib.backtesting.strategies.alpha_model_strategy.AlphaModelStrategy` through
the ``use_stop_losses=True`` flag and the ``fraction_at_risk`` field of each
:class:`~qf_lib.backtesting.alpha_model.alpha_model.AlphaModel`.

How stop losses are calculated
================================
When ``use_stop_losses=True``, the strategy computes a stop-loss price for every open position:

* **Long** position: ``stop_price = entry_price * (1 - fraction_at_risk)``
* **Short** position: ``stop_price = entry_price * (1 + fraction_at_risk)``

The ``fraction_at_risk`` is a property of the alpha model - it is typically estimated from recent
Average True Range (ATR) normalised by price. The ``risk_estimation_factor`` parameter on the alpha
model scales this estimate.

Enabling stop losses
======================
.. code-block:: python

    import matplotlib.pyplot as plt
    plt.ion()

    from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
        CalculateAndPlaceOrdersRegularEvent
    from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
    from qf_lib.backtesting.strategies.alpha_model_strategy import AlphaModelStrategy
    from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date
    from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
    from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter

    from demo_scripts.backtester.moving_average_alpha_model import MovingAverageAlphaModel
    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
    from demo_scripts.demo_configuration.demo_settings import get_demo_settings

    def main():
        start_date = str_to_date('2016-01-01')
        end_date = str_to_date('2017-12-31')

        settings = get_demo_settings()
        pdf_exporter = PDFExporter(settings)
        excel_exporter = ExcelExporter(settings)

        session_builder = BacktestTradingSessionBuilder(settings, pdf_exporter, excel_exporter)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_data_provider(daily_data_provider)
        session_builder.set_backtest_name("Stop Loss Demo")

        # Use InitialRiskPositionSizer - sizes positions so that the stop loss means
        # at most 3% of portfolio is at risk per trade
        session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk=0.03)

        ts = session_builder.build(start_date, end_date)

        model = MovingAverageAlphaModel(
            fast_time_period=5,
            slow_time_period=20,
            risk_estimation_factor=1.25,   # scales the ATR estimate used as fraction_at_risk
            data_provider=ts.data_provider,
        )

        model_tickers_dict = {model: [DummyTicker('AAA'), DummyTicker('BBB')]}

        # Enable stop losses here
        strategy = AlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=True)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

.. tip::
    Stop losses work best with
    :class:`~qf_lib.backtesting.position_sizer.initial_risk_position_sizer.InitialRiskPositionSizer`.
    That sizer calculates position size so that if the stop loss is hit, the portfolio loses at most
    ``initial_risk`` percent of its value - making risk per trade predictable.


*******************************************************
How to trade multiple assets with Alpha Models
*******************************************************

Trading multiple tickers simultaneously requires only a list of tickers in ``model_tickers_dict``.
The ``AlphaModelStrategy`` calls ``calculate_exposure()`` for each ticker independently every bar.

Multiple tickers with a single model
======================================
.. code-block:: python

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.backtester.moving_average_alpha_model import MovingAverageAlphaModel

    tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC'),
               DummyTicker('DDD'), DummyTicker('EEE')]

    model = MovingAverageAlphaModel(
        fast_time_period=5, slow_time_period=20,
        risk_estimation_factor=1.25, data_provider=ts.data_provider,
    )

    # Map one model to all five tickers
    model_tickers_dict = {model: tickers}

    strategy = AlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=True)

Multiple models, each covering different tickers
==================================================
You can also run several models in parallel. Each model is responsible for its own subset of tickers:

.. code-block:: python

    fast_model = MovingAverageAlphaModel(5, 20, 1.25, ts.data_provider)
    slow_model = MovingAverageAlphaModel(10, 50, 1.25, ts.data_provider)

    model_tickers_dict = {
        fast_model: [DummyTicker('AAA'), DummyTicker('BBB')],
        slow_model: [DummyTicker('CCC'), DummyTicker('DDD')],
    }

    strategy = AlphaModelStrategy(ts, model_tickers_dict)

Pre-loading data for multiple tickers
=======================================
When running with many tickers, pre-loading all price data before the backtest loop avoids repeated
network calls and speeds things up significantly:

.. code-block:: python

    all_tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC')]

    # Builds a PrefetchingDataProvider internally over the backtest date range
    ts.use_data_preloading(all_tickers)

    ts.start_trading()


*******************************************************
How to use order filters
*******************************************************

An :class:`~qf_lib.backtesting.orders_filter.orders_filter.OrdersFilter` intercepts orders just before
they are sent to the broker and adjusts or removes them based on custom criteria. The most common built-in
filter is :class:`~qf_lib.backtesting.orders_filter.volume_orders_filter.VolumeOrdersFilter`, which
caps each order's quantity so it does not exceed a given fraction of the asset's average daily volume.

Adding a VolumeOrdersFilter
=============================
.. code-block:: python

    from qf_lib.backtesting.orders_filter.volume_orders_filter import VolumeOrdersFilter
    from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder

    session_builder = BacktestTradingSessionBuilder(settings, pdf_exporter, excel_exporter)
    session_builder.set_frequency(Frequency.DAILY)
    session_builder.set_data_provider(daily_data_provider)

    # Limit each order to at most 10% of the 5-day average daily volume
    session_builder.add_orders_filter(VolumeOrdersFilter, volume_percentage_limit=0.10)

    ts = session_builder.build(start_date, end_date)

.. note::
    Slippage models also support volume limiting via the ``max_volume_share_limit`` parameter (see
    :doc:`customize_your_backtest`). The key difference is that
    :class:`~qf_lib.backtesting.orders_filter.volume_orders_filter.VolumeOrdersFilter` **cancels the
    excess quantity** before the order reaches the simulated exchange, whereas the slippage
    ``max_volume_share_limit`` limits the **fill** at execution time. Depending on your model, you may
    want to use both, one, or neither.

Writing a custom order filter
===============================
To implement your own filter, subclass
:class:`~qf_lib.backtesting.orders_filter.orders_filter.OrdersFilter` and implement ``adjust_orders()``:

.. code-block:: python

    from typing import List
    from qf_lib.backtesting.order.order import Order
    from qf_lib.backtesting.orders_filter.orders_filter import OrdersFilter

    class MaxPositionsFilter(OrdersFilter):
        """Rejects all new orders if the portfolio already holds max_positions assets."""

        def __init__(self, data_provider, max_positions: int):
            super().__init__(data_provider)
            self.max_positions = max_positions

        def adjust_orders(self, orders: List[Order]) -> List[Order]:
            # Count currently open positions via the data_provider or external state
            # (This is a simplified illustration - in practice you would inspect ts.portfolio)
            buy_orders = [o for o in orders if o.quantity > 0]
            sell_orders = [o for o in orders if o.quantity < 0]

            if len(buy_orders) > self.max_positions:
                # Keep only the first max_positions buy orders
                buy_orders = buy_orders[: self.max_positions]

            return buy_orders + sell_orders


*******************************************************
How to export results to Excel and PDF
*******************************************************

Excel export
=============
:class:`~qf_lib.documents_utils.excel.excel_exporter.ExcelExporter` writes any
:class:`~qf_lib.containers.dataframe.qf_dataframe.QFDataFrame` or
:class:`~qf_lib.containers.series.qf_series.QFSeries` to an ``.xlsx`` file:

.. code-block:: python

    from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
    from demo_scripts.demo_configuration.demo_settings import get_demo_settings

    settings = get_demo_settings()
    excel_exporter = ExcelExporter(settings)

    # Assuming prices_df is a QFDataFrame of close prices
    excel_exporter.export_container(
        container=prices_df,
        file_path="output/prices.xlsx",
        sheet_name="Close Prices",
    )

Excel import
=============
:class:`~qf_lib.documents_utils.excel.excel_importer.ExcelImporter` reads a sheet back into a
:class:`~qf_lib.containers.dataframe.qf_dataframe.QFDataFrame`:

.. code-block:: python

    from qf_lib.documents_utils.excel.excel_importer import ExcelImporter
    from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame

    excel_importer = ExcelImporter(settings)

    df = excel_importer.import_container(
        file_path="output/prices.xlsx",
        starting_cell="A1",
        ending_cell="B25",
        sheet_name="Close Prices",
        container_type=QFDataFrame,
    )

PDF export
===========
Tearsheets and analysis sheets are built on top of
:class:`~qf_lib.documents_utils.document_exporting.pdf_exporter.PDFExporter`. In most cases you do
not need to interact with it directly - just pass it to the tearsheet constructor and call
``tearsheet.save()``. See :doc:`analysing_backtest_results` for full examples.


*******************************************************
How to suppress backtest output
*******************************************************

By default, each backtest writes several files to the output directory. During a parameter sweep or unit
test this is undesirable. Use ``BacktestMonitorSettings.no_stats()`` to disable all file output:

.. code-block:: python

    from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitorSettings

    session_builder.set_monitor_settings(BacktestMonitorSettings.no_stats())

This keeps the portfolio in-memory (``ts.portfolio``) fully functional so you can still read
``ts.portfolio.portfolio_eod_series()`` and ``ts.portfolio.closed_positions()`` after the backtest.




