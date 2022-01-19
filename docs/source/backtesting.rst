backtesting
************
.. currentmodule:: qf_lib.backtesting

alpha_model
============
.. currentmodule:: qf_lib.backtesting.alpha_model

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    alpha_model.AlphaModel
    futures_model.FuturesModel

contract
==========
.. currentmodule:: qf_lib.backtesting.contract

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    contract_to_ticker_conversion.base.ContractTickerMapper
    contract_to_ticker_conversion.simulated_contract_ticker_mapper.SimulatedContractTickerMapper
    contract_to_ticker_conversion.ib_contract_ticker_mapper.IBContractTickerMapper


data_handler
==================
.. currentmodule:: qf_lib.backtesting.data_handler

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    data_handler.DataHandler
    daily_data_handler.DailyDataHandler
    intraday_data_handler.IntradayDataHandler

events
========
.. currentmodule:: qf_lib.backtesting.events.time_event

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    time_event.TimeEvent
    regular_time_event.regular_time_event.RegularTimeEvent
    regular_time_event.daily_market_event.DailyMarketEvent
    regular_time_event.after_market_close_event.AfterMarketCloseEvent
    regular_time_event.before_market_open_event.BeforeMarketOpenEvent
    regular_time_event.market_close_event.MarketCloseEvent
    regular_time_event.market_open_event.MarketOpenEvent

execution_handler
====================

commission_models
-----------------------
.. currentmodule:: qf_lib.backtesting.execution_handler.commission_models

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    commission_model.CommissionModel
    fixed_commission_model.FixedCommissionModel
    bps_trade_value_commission_model.BpsTradeValueCommissionModel
    ib_commission_model.IBCommissionModel

slippage
-----------
.. currentmodule:: qf_lib.backtesting.execution_handler.slippage

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    base.Slippage
    fixed_slippage.FixedSlippage
    price_based_slippage.PriceBasedSlippage
    square_root_market_impact_slippage.SquareRootMarketImpactSlippage


fast_alpha_model_tester
=========================
.. currentmodule:: qf_lib.backtesting.fast_alpha_model_tester

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    backtest_summary.BacktestSummaryElement
    fast_alpha_models_tester.FastAlphaModelTester
    fast_data_handler.FastDataHandler
    initial_risk_stats.InitialRiskStatsFactory
    scenarios_generator.ScenariosGenerator

monitoring
============
.. currentmodule:: qf_lib.backtesting.monitoring

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    abstract_monitor.AbstractMonitor
    backtest_monitor.BacktestMonitor
    backtest_result.BacktestResult

order
==========
.. currentmodule:: qf_lib.backtesting.order

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    execution_style.ExecutionStyle
    execution_style.MarketOrder
    execution_style.MarketOnCloseOrder
    execution_style.StopOrder
    order_factory.OrderFactory
    order.Order
    time_in_force.TimeInForce

orders_filter
==================
.. currentmodule:: qf_lib.backtesting.orders_filter

.. autosummary::
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst


    orders_filter.OrdersFilter
    volume_orders_filter.VolumeOrdersFilter

portfolio
===========
.. currentmodule:: qf_lib.backtesting.portfolio

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    portfolio.Portfolio
    backtest_position.BacktestPosition
    trade.Trade
    transaction.Transaction

position_sizer
===============
.. currentmodule:: qf_lib.backtesting.position_sizer

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    position_sizer.PositionSizer
    simple_position_sizer.SimplePositionSizer
    initial_risk_position_sizer.InitialRiskPositionSizer
    initial_risk_with_volume_position_sizer.InitialRiskWithVolumePositionSizer
    fixed_portfolio_percentage_position_sizer.FixedPortfolioPercentagePositionSizer

signals
=====================
.. currentmodule:: qf_lib.backtesting.signals

.. autosummary::
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    signal.Signal
    signals_register.SignalsRegister
    backtest_signals_register.BacktestSignalsRegister

strategies
=====================
.. currentmodule:: qf_lib.backtesting.strategies

.. autosummary::
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    abstract_strategy.AbstractStrategy
    alpha_model_strategy.AlphaModelStrategy
    signal_generators.OnBeforeMarketOpenSignalGeneration

trading_session
=====================
.. currentmodule:: qf_lib.backtesting.trading_session

.. autosummary::	
    :nosignatures:
    :toctree: _autosummary
    :template: short_class.rst

    trading_session.TradingSession
    backtest_trading_session.BacktestTradingSession
    backtest_trading_session_builder.BacktestTradingSessionBuilder
